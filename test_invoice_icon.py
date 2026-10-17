# -*- coding: utf-8 -*-
"""test_invoice_icon.py - round SB-1, 17 Oct 2026.

ONE DOCUMENT, TWO SCREENS, TWO ICONS.

Demetri, 17 Oct: the Invoice icon in the Actual Expenses table reached
through Financial Management must match the one reached through
Property Operations. They are the same table and the same document.

They were not the same icon:

                     act_expense.html        property_detail.html
    class            report-invoice-icon     invoice-icon
    colour           --alv-view, from CSS    --alv-good, INLINE
    size             inherited               font-size: 1.2em, INLINE
    opens via        data attributes and     an inline onclick
                     one delegated listener
    no invoice       an em dash in a         a hyphen in .text-muted
                     named class

AND IT WAS NOT A NEW DECISION. act_expense.html carries the reason in
its own stylesheet: "Viewing a document is the VIEW verb, and base has
a colour for it. This was #28a745 - Bootstrap's success green - which
said 'good' about an icon that only opens a file." property_detail was
still wearing that fault in a token's clothing.

WHAT THIS SUITE PROVES THAT READING THE MARKUP CANNOT

    Section 4 puts the SAME markup under each page's stylesheet in turn
    and reads the computed colour, size and cursor off both. "The two
    rules are identical" is a text claim; "the icon computes the same
    under either page" is the claim Demetri actually made, and only a
    browser can answer it.

    Section 2 asserts the two rules character for character rather than
    equivalently, because the fault here was a correction landing on
    one page and not the other. Two rules that merely agree today can
    drift apart tomorrow; two that are the same line cannot.
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

SUFFIX = '.bak_invoiceicon'
PAGE = 'property_detail.html'
MODEL = 'act_expense.html'
ME = 'test_invoice_icon.py'
PATCHER = 'apply_invoice_icon.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CONVERTED_NOW, ALIAS_NOW = 99, 107

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


def as_sb1_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


PATH = alv_tree.path_of(PAGE)
NOW = read(PATH)
APPLIED = os.path.isfile(PATH + SUFFIX)
WAS = read(PATH + SUFFIX) if APPLIED else NOW
B_NOW, B_WAS = code_only(NOW), code_only(WAS)
MODEL_SRC = read(alv_tree.path_of(MODEL))
B_MODEL = code_only(MODEL_SRC)

print('')
print('test_invoice_icon.py - round SB-1, 17 Oct 2026')
print('  page     : %s   (Property Operations route)' % PAGE)
print('  model    : %s      (Financial Management route)' % MODEL)
print('  state    : %s' % ('APPLIED - backup on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same file, and the CONTROLs will say so'))


# ==========================================================================
head('1. THE SAME ICON, WHICHEVER ROUTE REACHES THE TABLE')
# ==========================================================================
# Demetri reached one Actual Expenses table from two menus and got two
# different icons. These are the four things that differed.
ok('report-invoice-icon' in B_NOW,
   '%s now draws the class %s draws' % (PAGE, MODEL))
ok(not re.search(r'(?<!report-)\binvoice-icon\b', B_NOW),
   '  and nothing is left of the old class')
ok(not APPLIED or re.search(r'(?<!report-)\binvoice-icon\b', B_WAS),
   'CONTROL: it had a class of its own, until this round')

ok('font-size: 1.2em' not in B_NOW,
   'the glyph is no longer sized inline')
ok(not APPLIED or 'font-size: 1.2em' in B_WAS,
   'CONTROL: it was a fifth bigger than the other route')

ok('onclick="viewActualExpense' not in B_NOW,
   'and it no longer opens from an inline onclick')
ok(not APPLIED or 'onclick="viewActualExpense' in B_WAS,
   'CONTROL: it did')

ok('data-invoice-url' in B_NOW and 'data-filename' in B_NOW,
   'it carries the two attributes the other route reads')
ok('report-invoice-none' in B_NOW and '&mdash;' in B_NOW,
   'and draws an em dash in a named class when there is no document')
ok(not APPLIED or '<span class="text-muted">-</span>' in B_WAS,
   'CONTROL: it drew a hyphen in .text-muted - the spelling TD-2 took '
   'off the title deeds table on 16 Oct')


# ==========================================================================
head('2. THE RULES ARE THE MODEL\'S, VERBATIM')
# ==========================================================================
# Not "equivalent". The same two lines, so a round that changes one page
# cannot leave the other behind again - which is the whole fault here.
for rule in ('.report-invoice-icon { cursor: pointer; color: var(--alv-view); }',
             '.report-invoice-none { color: var(--alv-ink-faint); }'):
    ok(rule in B_MODEL, '%s declares %s' % (MODEL, rule.split(' {')[0]))
    ok(rule in B_NOW, '  and so does %s, character for character' % PAGE)

# THE COLOUR IS THE VERB, NOT A VERDICT.
ok('--alv-view' in read(alv_tree.path_of('base.html')),
   'base declares --alv-view, the colour of the VIEW verb')
icon_area = B_NOW[max(0, B_NOW.find('.report-invoice-icon') - 600):
                  B_NOW.find('.report-invoice-icon') + 400]
ok(not re.search(r'(?:color|background)\s*:\s*var\(--alv-good[^)]*\)', icon_area),
   'and no green declaration survives beside the icon rules')
ok(not APPLIED or 'color: var(--alv-good-ink) !important' in B_WAS,
   'CONTROL: the hover forced --alv-good-ink with !important')
ok('transform: scale(1.2)' not in B_NOW,
   'and the hover no longer grows the glyph - nothing else in this '
   'application does')


# ==========================================================================
head('3. ONE LISTENER, AND IT OPENS SOMETHING')
# ==========================================================================
scripts = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>',
                               B_NOW, re.S))
ok("closest('.report-invoice-icon')" in scripts,
   'a delegated listener reads the class')
ok("getAttribute('data-invoice-url')" in scripts,
   '  and the attribute, not an argument baked into the markup')
# THE FALLBACK. PL-1, 5 Oct: an icon that does nothing when pressed is
# worse than the unfindable tick it replaced, which at least worked.
ok("window.open(documentUrl, '_blank')" in scripts,
   'and a viewer that has not loaded opens a tab rather than nothing')
ok(not APPLIED or "console.error('PDF viewer component not loaded')" in B_WAS,
   'CONTROL: it wrote to the console and returned')
m_scripts = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>',
                                 B_MODEL, re.S))
ok('window.open(documentUrl' in m_scripts
   or 'window.open(url' in m_scripts,
   '  which is what %s has always done' % MODEL)


# ==========================================================================
head('4. RENDERED - BOTH ROUTES DRAW ONE COLOUR AND ONE SIZE')
# ==========================================================================
# The claim is a RELATION between two renders in one browser: the icon
# from this page and the icon from the model page must compute the same.
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

LOOK = """() => {
  const g = e => getComputedStyle(e);
  const one = document.getElementById('a');
  const two = document.getElementById('b');
  const none1 = document.getElementById('na');
  const none2 = document.getElementById('nb');
  const pick = e => ({color: g(e).color, size: g(e).fontSize,
                      cursor: g(e).cursor});
  return {a: pick(one), b: pick(two),
          na: g(none1).color, nb: g(none2).color,
          naText: none1.textContent.trim(),
          nbText: none2.textContent.trim()};
}"""


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S | re.I))


if not have_pw or not os.path.isfile(BOOT):
    skip('both icons in a browser', 'playwright or the fixture is absent')
else:
    from playwright.sync_api import sync_playwright

    base_css = css_of(read(alv_tree.path_of('base.html')))
    body = ('<table><tr>'
            '<td><i id="a" class="fas fa-file-alt report-invoice-icon"></i>'
            '</td>'
            '<td><span id="na" class="report-invoice-none">&mdash;</span>'
            '</td></tr></table>'
            '<table><tr>'
            '<td><i id="b" class="fas fa-file-alt report-invoice-icon"></i>'
            '</td>'
            '<td><span id="nb" class="report-invoice-none">&mdash;</span>'
            '</td></tr></table>')
    fx = os.path.join(SCRATCH, 'sb1.html')
    with open(fx, 'w', encoding='utf-8') as f:
        # THE TWO PAGES' OWN STYLESHEETS, one after the other, so a rule
        # that differs between them shows as a difference here.
        f.write('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>'
                '<div style="display:none"></div></head><body>'
                '<div class="main-content">%s</div>'
                '<style>%s</style></body></html>'
                % (read(BOOT), base_css, body, css_of(B_NOW)))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 1280, 'height': 700})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        pg.wait_for_timeout(80)
        r = pg.evaluate(LOOK)
        ctx.close()

        # And the same markup under the MODEL page's stylesheet.
        with open(fx, 'w', encoding='utf-8') as f:
            f.write('<!doctype html><html><head><meta charset="utf-8">'
                    '<style>%s</style><style>%s</style></head><body>'
                    '<div class="main-content">%s</div>'
                    '<style>%s</style></body></html>'
                    % (read(BOOT), base_css, body, css_of(B_MODEL)))
        ctx = br.new_context(viewport={'width': 1280, 'height': 700})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        pg.wait_for_timeout(80)
        rm = pg.evaluate(LOOK)
        ctx.close()
        br.close()

    print('      under %s : %s  %s' % (PAGE, r['a']['color'],
                                       r['a']['size']))
    print('      under %s    : %s  %s' % (MODEL, rm['a']['color'],
                                          rm['a']['size']))
    ok(r['a']['color'] == rm['a']['color'],
       'the icon computes the SAME COLOUR under both stylesheets: %s'
       % r['a']['color'], (r['a']['color'], rm['a']['color']))
    ok(r['a']['size'] == rm['a']['size'],
       '  and the same size: %s' % r['a']['size'],
       (r['a']['size'], rm['a']['size']))
    ok(r['a']['cursor'] == rm['a']['cursor'] == 'pointer',
       '  and both say it can be clicked')
    ok(r['na'] == rm['na'],
       'the empty state matches too: %s' % r['na'], (r['na'], rm['na']))
    ok(r['naText'] == rm['naText'] == '—',
       '  and both draw an em dash, not a hyphen')


# ==========================================================================
head('5. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(SUFFIX in _r and '.bak_contactmodal' in _r
       and _r.index(SUFFIX) > _r.index('.bak_contactmodal'),
       '  and sits after .bak_contactmodal', _r[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s runs this suite' % PS1)
ok("Text = 'report-invoice-icon'" in ps1,
   'and holds a sentinel on the shared class')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

bad = [i + 1 for i, ln in enumerate(NOW.split('\n'))
       if ln.count('{#') != ln.count('#}')]
ok(not bad, 'every {# comment on the page closes on its own line', bad)

wd = as_sb1_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when SB-1 left it'
   % CONVERTED_NOW)
co = as_sb1_left('test_code_only.py')
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counted %d files aliasing code_only' % ALIAS_NOW)


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if failed:
    print('')
    print('  WHAT THIS ROUND IS, in one line:')
    print('  One Actual Expenses table, reached from two menus, drew two')
    print('  different Invoice icons - different class, different colour,')
    print('  a fifth bigger, and an inline onclick. act_expense had')
    print('  already been corrected off the green; this is where that')
    print('  correction finishes.')
sys.exit(1 if failed else 0)
