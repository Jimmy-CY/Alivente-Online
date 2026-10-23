# -*- coding: utf-8 -*-
"""test_notify_icon.py - round NV-1c, 16 Oct 2026.

A VERB THE VOCABULARY DID NOT HAVE.

Demetri: "I think that I want to change the Edit and Notify Now Buttons
to be inline with our standards. We have a standard for Edit. We will
need to create a standard for Notify (maybe just a bell with a Notify
Now hover)."

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT
    Section 2 proves .icon-notify is .icon-lock's rule DECLARATION FOR
    DECLARATION, so "a new name on an existing colour" is measured and
    not claimed.
    Section 6 renders the strip at desktop and at a phone, because
    icon-only AT EVERY WIDTH is only safe while base keeps .row-actions
    out of its 768px block - and section 1 of the patcher refuses if it
    ever stops.

SECTION 1 SKIPS RATHER THAN RAISES. On a tree without this round the
vocabulary has no `notify`, and comparing an int with None is a
traceback instead of a verdict - the fifth suite this month to do that.
A crash blocks a push exactly as hard as a failure and says less about
why. See step 4 of claude/standard_delivery_preflight.md.

NUMBERS, AND WHICH MACHINE MEASURED THEM
    The one pixel literal asserted here is 44x44, and it is a DECLARED
    BOX: base sets `width: 44px; height: 44px` on .icon-action-btn inside
    its 768px block, and the button holds a glyph and no text. No font
    can move it. Everything else is a colour, a count or a relation; see
    the sixth failure in the pre-flight doc for why that distinction is
    a rule here.

WHAT THIS ROUND DOES NOT PROVE
    That .status-btn should go away. It is base's inline button and
    plenty of pages use it correctly; what was wrong here is that a
    ROW-ACTION STRIP was wearing it.
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

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by  # noqa: F401
except Exception as e:
    as_left_by = None
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only

SUFFIX = '.bak_notifyicon'
BASEP = 'base.html'
PAGE = 'fsr_details.html'
IPAGE = 'physical_invoice_list.html'
ME = 'test_notify_icon.py'
PATCHER = 'apply_notify_icon.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CONVERTED_NOW, ALIAS_NOW = 87, 85
NOTE = 'NV-1c, 16 Oct 2026 - '
ROW_N, LOOSE_N = 113, 83
TAP = 44

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
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S))


def js_of(t):
    return '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>', t, re.S))


def decls(css, sel):
    """The declarations of one rule, normalised, or None."""
    m = re.search(r'(?m)^[ \t]*' + re.escape(sel) + r'\s*\{([^}]*)\}', css)
    if not m:
        return None
    out = []
    for d in m.group(1).split(';'):
        d = ' '.join(d.split())
        if d:
            out.append(d)
    return out


def at_block(css, opener):
    """EVERY block that matches, joined - base has several 768px ones.

    The first cut of this helper returned only the first, so the 44px
    tap-target rule - which lives in the last of them - read as absent.
    """
    out = []
    for m in re.finditer(opener, css):
        depth, j = 1, m.end()
        while depth and j < len(css):
            if css[j] == '{':
                depth += 1
            elif css[j] == '}':
                depth -= 1
            j += 1
        out.append(css[m.end():j - 1])
    return '\n'.join(out) if out else None


BPATH = alv_tree.path_of(BASEP)
PATH = alv_tree.path_of(PAGE)
IPATH = alv_tree.path_of(IPAGE)

BASE = read(BPATH)
C_BASE = css_of(code_only(BASE))
NOW, INOW = read(PATH), read(IPATH)
# A ROUND'S OWN BEFORE IS ITS OWN BACKUP, read directly.
WAS = read(PATH + SUFFIX) if os.path.isfile(PATH + SUFFIX) else read(PATH)
IWAS = (read(IPATH + SUFFIX) if os.path.isfile(IPATH + SUFFIX)
        else read(IPATH))
B_NOW, B_WAS = code_only(NOW), code_only(WAS)
IB_NOW, IB_WAS = code_only(INOW), code_only(IWAS)
C_NOW, C_WAS = css_of(B_NOW), css_of(B_WAS)
J_NOW, J_WAS = js_of(B_NOW), js_of(B_WAS)


# ==========================================================================
head('1. WHERE NOTIFY SORTS, AND IT IS NOT THE MARKUP THAT SAYS SO')
# ==========================================================================
# GUARDED, BECAUSE A MISSING VERB IS NOT A CRASH. Backed out, the
# vocabulary has no `notify` and FAMILY['edit'] < None raises - which is
# a traceback instead of a verdict, and the fifth suite this month to do
# it.
try:
    import alv_rowactions as ra
except Exception as e:
    ra = None
    skip('the vocabulary', 'alv_rowactions: %s' % e)

if ra is None:
    pass
elif ra.FAMILY.get('notify') is None:
    skip('where notify sorts', 'the vocabulary does not have the verb, '
                               'so this round is not applied here')
else:
    _n = ra.FAMILY['notify']
    ok(_n == ra.ADVANCE,
       'notify is ADVANCE - the record moves on, beside send', _n)
    ok(ra.FAMILY['edit'] < _n,
       '  and Edit is CHANGE (%d), so the strip reads edit then notify '
       'without the markup being told that' % ra.FAMILY['edit'])
    ok(_n < ra.FAMILY['delete'],
       '  while DESTROY (%d) is still last' % ra.FAMILY['delete'])
    # THE FAMILY SPLITS BY CONSEQUENCE, which is what chose the colour.
    warn = [k for k in ('unapprove', 'lock', 'reset-pw')
            if ra.FAMILY.get(k) == ra.ADVANCE]
    ok(len(warn) == 3,
       '  and three other ADVANCE verbs are the warn group it joins: %s'
       % ', '.join(warn), warn)


# ==========================================================================
head('2. .icon-notify IS .icon-lock\'S RULE UNDER ITS OWN NAME')
# ==========================================================================
for suffix in ('', ':hover'):
    a = decls(C_BASE, '.icon-notify' + suffix)
    b = decls(C_BASE, '.icon-lock' + suffix)
    ok(a is not None, 'base declares .icon-notify%s' % suffix)
    ok(a == b,
       '  and its declarations are .icon-lock%s\'s exactly - a new NAME '
       'on an existing colour, not a new colour' % suffix,
       '%s\n       vs %s' % (a, b))
ok(decls(C_BASE, '.icon-color-notify') == decls(C_BASE, '.icon-color-lock'),
   'and so is .icon-color-notify, for the phone bar glyph')

ok(all('--alv-warn' in d for d in (decls(C_BASE, '.icon-notify') or [''])),
   'the tone is --alv-warn, which in base means SOMEBODY WILL NOTICE - '
   'the group .icon-unapprove, .icon-lock and .icon-reset-pw are in',
   decls(C_BASE, '.icon-notify'))
ok('--alv-accent' not in ' '.join(decls(C_BASE, '.icon-notify') or []),
   '  and NOT the accent, which is .icon-send - a thing going out is '
   'not the same as a thing people will be told about')

# A CLASS CARRIES ONE PICTURE, which is why it is not .icon-lock.
ok('fa-bell' in B_NOW and 'fa-bell' not in C_BASE,
   'the picture is fa-bell, and it is in the markup - base colours a '
   'name, it does not choose a glyph')


# ==========================================================================
head('3. BOTH CONTROLS ARE ICON-ONLY, AND THE HOOKS SURVIVED')
# ==========================================================================
ok('status-btn' not in B_NOW,
   'the page carries no status-btn at all now')
ok(B_WAS.count('status-btn') == 4,
   'CONTROL: it carried four - two buttons and two page-local rules',
   B_WAS.count('status-btn'))
ok(B_NOW.count('class="row-actions"') == 1,
   'the two controls sit in ONE row-action strip',
   B_NOW.count('class="row-actions"'))
ok('row-actions' not in B_WAS,
   'CONTROL: and there was no strip before - they were loose buttons')

for cls, what in (('icon-edit', 'Edit'), ('icon-notify', 'Notify')):
    m = re.search(r'<button\b[^>]*\b%s\b[^>]*>(.*?)</button>' % cls,
                  B_NOW, re.S)
    ok(m is not None, '%-7s is an icon-action-btn %s' % (what, cls))
    if m:
        inner = re.sub(r'<i\b[^>]*>\s*</i>', '', m.group(1)).strip()
        ok(inner == '',
           '  and draws a glyph and nothing else - icon-only, which is '
           'what he asked for', repr(inner[:40]))
        ok('title=' in m.group(0) and 'aria-label=' in m.group(0),
           '  with a title for the hover and an aria-label for the rest')

ok('title="Notify Now"' in B_NOW,
   'the bell hover says Notify Now - "maybe just a bell with a Notify '
   'Now hover", in his words')

for hook in ('comment-edit-btn', 'notify-urgent-btn',
             'notify-urgent-cell', 'notified-badge'):
    ok(hook in B_NOW,
       'the JS hook %-19s survives - the classes that FIND are not the '
       'classes that PAINT' % hook)
    ok(hook in J_NOW or hook in B_NOW,
       '  and the script still names it')


# ==========================================================================
head('4. THE SPINNER, BECAUSE THE BUTTON IS A %dPX SQUARE NOW' % TAP)
# ==========================================================================
ok("btn.innerHTML = 'Sending...'" in J_WAS,
   'CONTROL: the script wrote a nine-character word into the button')
ok("'Sending...'" not in J_NOW, 'it does not any more')
ok('fa-spinner fa-spin' in J_NOW,
   'it writes a spinning glyph instead')
ok(J_NOW.count('btn.innerHTML = originalLabel') == 3,
   'and the three failure paths restore originalLabel unchanged',
   J_NOW.count('btn.innerHTML = originalLabel'))
# ASKED AS A MEMBERSHIP FIRST. str.index RAISES on a tree where this
# round is not applied, and a traceback is not a verdict - it blocks a
# push exactly as hard as a failure and says less about why. This is
# the same shape as the 15 Oct failure where section 4b reported the
# offender and then crashed ordering it.
_a = J_NOW.find('var originalLabel = btn.innerHTML')
_b = J_NOW.find('fa-spinner')
ok(_a >= 0 and _b >= 0 and _a < _b,
   '  which is read BEFORE the swap, so it is the bell and the failure '
   'paths needed nothing', (_a, _b))
# AND THE CELL'S OWN WRITE IS LEFT ALONE, because it is not a control.
ok(J_NOW.count('cell.innerHTML') == 2,
   'the two writes into the CELL are untouched - the Notified badge is '
   'not a 44px square and this round has no business there',
   J_NOW.count('cell.innerHTML'))


# ==========================================================================
head('5. AND THE PAGE SPELLS NO COLOUR BY HAND AT ALL')
# ==========================================================================
hex_now = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', C_NOW)))
hex_was = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', C_WAS)))
ok(hex_now == [],
   'no hex literal survives in this page stylesheet', hex_now)
ok(hex_was == ['#ecd9a8'],
   'CONTROL: and the one it had was #ecd9a8, the Notify tone\'s border',
   hex_was)
ok(re.search(r'(?m)^[ \t]*\.notify-urgent-btn', C_NOW) is None,
   'the page declares no appearance for the Notify button')
ok(re.search(r'(?m)^[ \t]*\.notify-urgent-btn\.status-btn', C_WAS)
   is not None,
   'CONTROL: and it declared a page-local tone, deliberately, with the '
   'condition for promoting it written down')

# THE TWO SUITES THAT RECORDED THAT EXCEPTION ARE RE-POINTED BY THIS
# ROUND'S PATCHER, because a round that falsifies a claim fixes it.
am = read(os.path.join(ROOT, 'test_amber.py'))
fp = read(os.path.join(ROOT, 'test_fsr_palette.py'))
ok("'#ecd9a8' not in T.code_only" in am,
   'test_amber reads the tint as retired, and still asserts B-4 left it '
   'alone - the restraint was the point of that section')
ok('B-4 did not touch that page at all' in am,
   '  which is the claim that did NOT change')
ok('allowed = []' in fp,
   'test_fsr_palette allows no literal on either page now')
ok("'#ecd9a8' not in DNC" in fp,
   '  and reads the tint as retired by the round that owned it')


# ==========================================================================
head('6. RENDERED - A BELL IN A %dPX SQUARE, AT EVERY WIDTH' % TAP)
# ==========================================================================
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

STRIP = ('<span class="row-actions">'
         '<button class="comment-edit-btn icon-action-btn icon-edit" '
         'title="Edit your comment"><i class="fas fa-pencil-alt"></i>'
         '</button>'
         '<span class="notify-urgent-cell">'
         '<button class="notify-urgent-btn icon-action-btn icon-notify" '
         'title="Notify Now"><i class="fas fa-bell"></i></button>'
         '</span></span>')

LOOK = """() => {
  const b = [...document.querySelectorAll('.icon-action-btn')];
  const r = document.querySelector('.row-actions');
  const box = e => e.getBoundingClientRect();
  return {n: b.length,
          sizes: b.map(e => Math.round(box(e).width) + 'x'
                          + Math.round(box(e).height)),
          colours: b.map(e => getComputedStyle(e).color),
          borders: b.map(e => getComputedStyle(e).borderTopColor),
          strip: getComputedStyle(r).display,
          tops: b.map(e => box(e).top),
          order: b.map(e => e.className.match(/icon-(edit|notify)/)[1])};
}"""


def tokval(name):
    m = re.search(r'--' + name + r'\s*:\s*(#[0-9a-fA-F]{3,6})', BASE)
    return m.group(1) if m else None


def rgb(hexv):
    h = hexv.lstrip('#')
    return 'rgb(%d, %d, %d)' % tuple(int(h[i:i + 2], 16)
                                     for i in (0, 2, 4))


if not have_pw or not os.path.isfile(BOOT):
    skip('the strip in a browser', 'playwright or the fixture is absent')
else:
    from playwright.sync_api import sync_playwright
    p = os.path.join(SCRATCH, 'strip.html')
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<meta name="viewport" content="width=device-width,'
                 'initial-scale=1"><style>%s</style><style>%s</style>'
                 '<style>body{margin:0;background:#fff}'
                 '*{transition:none !important}</style></head>'
                 '<body>%s</body></html>'
                 % (read(BOOT), C_BASE, STRIP))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        try:
            for w, what in ((1280, 'desktop'), (390, 'a phone')):
                ctx = br.new_context(viewport={'width': w, 'height': 500})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, p)
                pg.wait_for_timeout(50)
                m = pg.evaluate(LOOK)
                ok(m['n'] == 2,
                   '%-8s two controls draw' % what, m['n'])
                ok(m['strip'] == 'inline-flex',
                   '%-8s   the strip is SHOWN - base touches .row-actions '
                   'only at top level and in @media print, which is the '
                   'whole reason icon-only works at every width' % '',
                   m['strip'])
                # WITHIN A PIXEL, AND THE BAND IS THE POINT. Notify
                # sits inside .notify-urgent-cell, which the script
                # replaces wholesale and which computes to display:
                # block - so it is a 35px flex item beside a 34px one
                # and centring drops the bell half a pixel at desktop.
                # Math.round turned 1 and 1.5 into two lines and
                # reported a misalignment nobody can see. The claim is
                # ONE LINE, so the test is a relation with a band, the
                # way PJ-2's wrap law carries 4px of rounding.
                ok(max(m['tops']) - min(m['tops']) <= 1,
                   '%-8s   both on one line, within a pixel: %s'
                   % ('', m['tops']), m['tops'])
                ok(m['order'] == ['edit', 'notify'],
                   '%-8s   and in the vocabulary order: %s'
                   % ('', m['order']))
                if tokval('alv-warn'):
                    ok(m['colours'][1] == rgb(tokval('alv-warn')),
                       '%-8s   the bell computes to --alv-warn %s'
                       % ('', tokval('alv-warn')), m['colours'])
                ok(m['colours'][0] != m['colours'][1],
                   '%-8s   and does not look like Edit (%s)'
                   % ('', m['colours'][0]), m['colours'])
                if w == 390:
                    # THE ONE PIXEL LITERAL IN THIS FILE, and it is a
                    # DECLARED BOX: base sets width and height to 44px
                    # inside its 768px block and the button holds a
                    # glyph, not text. No font can move it.
                    ok(all(s == '%dx%d' % (TAP, TAP) for s in m['sizes']),
                       '%-8s   each is a %dpx tap target: %s'
                       % ('', TAP, m['sizes']), m['sizes'])
                ctx.close()
        finally:
            br.close()

    ok(re.search(r'\.icon-action-btn\s*\{\s*width:\s*%dpx;\s*height:\s*%dpx'
                 % (TAP, TAP),
                 at_block(C_BASE,
                          r'@media screen and \(max-width: 768px\)\s*\{')
                 or '') is not None,
       'and that %dpx is base DECLARING a box in its 768px block, which '
       'is why asserting it is not asserting a text width' % TAP)


# ==========================================================================
head('7. AND THE TENANT INVOICE ROW SAYS WHY IT HAS NO COPY')
# ==========================================================================
ok(IB_NOW.count("{% url 'customer_invoice_duplicate' row.pk %}") == 2,
   'the duplicate action is where it was, twice - the desktop strip and '
   'the phone bar',
   IB_NOW.count("{% url 'customer_invoice_duplicate' row.pk %}"))
ok(IB_WAS.count("{% url 'customer_invoice_duplicate' row.pk %}") == 2,
   '  CONTROL: and this round added neither of them - a customer '
   'invoice has been duplicable since it shipped')
ok(IB_NOW.count('icon-action-btn icon-disabled') == 1,
   'the disabled mirror is the desktop strip\'s alone: an action COLUMN '
   'should read one width per row, and the phone bar is a grid that '
   'sizes to its children',
   IB_NOW.count('icon-action-btn icon-disabled'))
ok('Duplicate is for customer invoices only' in IB_NOW,
   '  carrying the reason in its title')
ok('one per tenant per month' in IB_NOW,
   '  and the reason is the constraint, in words a reader can act on')
ok('{% elif perms.auth.can_edit_invoices %}' in IB_NOW,
   'and it is an elif on the SAME permission, so a reader who cannot '
   'edit sees neither the action nor a mirror of it')
ok('.icon-disabled' in C_BASE,
   'base owns the disabled look, so this is the house pattern and not a '
   'new one')


# ==========================================================================
head('8. REGISTERED, ON THE GATE')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok(ME in ps, '%s runs this suite' % PS1)
ok(ME in read(os.path.join(ROOT, 'alv_tree.py')),
   'alv_tree.CONVERTED names it')
ok(SUFFIX in read(os.path.join(ROOT, 'alv_rounds.py')),
   'alv_rounds.ROUNDS names %s' % SUFFIX)
ok("Text = '.icon-notify'" in ps,
   'and the gate carries a row for the icon being in base')
ok('Text = "\'notify\': ADVANCE"' in ps or "'notify': ADVANCE" in ps,
   '  one for the verb being in the vocabulary')
ok('Duplicate is for customer invoices only' in ps,
   '  and one for the tenant row saying why')
# A FLOOR, NOT A PIN. The sibling NV rounds ship in the same push and
# each moves these counters, so a suite that pins the number it set
# fails the moment its sibling applies. The house shape is `at least`,
# plus the round's OWN NOTE, which is permanent.
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
co = read(os.path.join(ROOT, 'test_code_only.py'))
bh = read(os.path.join(ROOT, 'test_bar_height.py'))
ok(NOTE + 'this round own suite' in wd,
   "the converted count carries this round's note")
ok(NOTE + 'this round own patcher and suite' in co,
   'and so does the alias count')
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  and CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
ok(NOTE + 'the physical invoice disabled mirror' in bh,
   'the table-row census carries this round\'s note - the mirror sits '
   'in the desktop strip, which is inside a table')
ok(NOTE + 'the two comment controls' in bh,
   'and the LOOSE census carries its own - the two comment controls '
   'were .status-btn, which that census does not select, and a comment '
   'thread is not a table')
# THE ROW COUNT, NOT THE OTHER TWO - RV-1, 23 Oct 2026.
# This read `= 267, (\d+), 95`, pinning the BAR and MODAL
# counts incidentally. RV-1 adds a page whose bar carries
# three controls, N_BAR moved 267 -> 270, and the claim
# failed on a number it does not care about.
_r = re.search(r'N_BAR, N_ROW, N_MODAL = \d+, (\d+), \d+', bh)
_l = re.search(r'N_LOOSE, N_LOOSE_H = (\d+), 11', bh)
ok(_r and int(_r.group(1)) >= ROW_N,
   '  the live table-row count is at least %d' % ROW_N,
   _r.group(1) if _r else None)
ok(_l and int(_l.group(1)) >= LOOSE_N,
   '  and the loose count is at least %d, with N_LOOSE_H still 11 '
   'because 34px was already one of its eleven heights' % LOOSE_N,
   _l.group(1) if _l else None)


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NV-1c: Notify is a verb the vocabulary did not have. It is')
print('  ADVANCE - the record moves on - and ADVANCE splits by')
print('  CONSEQUENCE, so the bell is --alv-warn and not the accent:')
print('  Notify Now emails everyone configured except the clicker.')
print('')
print('  .icon-notify is .icon-lock\'s rule under its own name, because a')
print('  class carries one picture. The page had reached the same')
print('  reading on its own, page-locally; this moves that decision to')
print('  where the other forty-one live, and fsr_details now spells no')
print('  colour by hand at all.')
print('')
print('  And a tenant invoice row says, on the screen, why it has no')
print('  Duplicate: unique_together makes it one per tenant per month.')
print('')
sys.exit(1 if failed else 0)
