# -*- coding: utf-8 -*-
"""test_contact_modal.py - round CC-2, 17 Oct 2026.

THE CONTACT OPENS IN A MODAL, NOT IN PLACE.

Decided 15 Oct, built now. In the compact view a click toggled
`.expanded` on the card, which revealed the email, phone and notes, the
whole event list AND the action strip - growing the card and pushing
every card after it down the grid.

WHAT THIS SUITE PROVES THAT READING THE MARKUP CANNOT

    Section 4 draws three cards, switches to the compact view, clicks
    the first, and asserts THE TWO BELOW IT DO NOT MOVE. Then it draws
    the same page from the backup and shows that they did. That is the
    request, stated as a relation between two renders rather than as a
    pixel.

    It also asserts the modal opened with that contact's name, its
    details and its events - because a grid that does not move and a
    modal that is empty would pass a weaker claim.

WHAT THE ROUND DOES NOT TOUCH

    `#contactModal`, the Add/Edit form, which was ALREADY a modal. The
    15 Oct note reads as though the form were the problem; measuring
    first showed it was not. Section 1 asserts that modal is unchanged
    byte for byte.

AND THE EMOJI

    CC-1 took the calendar's countdown emoji on 15 Oct and wrote down
    why: nothing else in this application puts an emoji in its chrome.
    These are the same four states on the sibling page. Section 3
    asserts the words match the calendar's, so the two pages count down
    in one voice - and that both carry the same reason in the same
    words.
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

SUFFIX = '.bak_contactmodal'
PAGE = 'celebration_management.html'
MODEL = 'celebration_calendar.html'
ME = 'test_contact_modal.py'
PATCHER = 'apply_contact_modal.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
JQ = os.path.join(ROOT, 'test_fixture_jquery360.js')
BSJS = os.path.join(ROOT, 'test_fixture_bootstrap413.js')

CONVERTED_NOW, ALIAS_NOW = 98, 105
EMOJI = ('\U0001F389', '\U0001F4C5', '⚡', '\U0001F4C6')

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


def as_cc2_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


PATH = alv_tree.path_of(PAGE)
NOW = read(PATH)
APPLIED = os.path.isfile(PATH + SUFFIX)
WAS = read(PATH + SUFFIX) if APPLIED else NOW
B_NOW, B_WAS = code_only(NOW), code_only(WAS)

print('')
print('test_contact_modal.py - round CC-2, 17 Oct 2026')
print('  page     : %s' % PAGE)
print('  state    : %s' % ('APPLIED - backup on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same file, and the CONTROLs will say so'))


# ==========================================================================
head('1. THE CONTACT OPENS IN A MODAL')
# ==========================================================================
ok(B_NOW.count('id="contactDetailModal"') == 1,
   'the page declares one contact detail modal',
   B_NOW.count('id="contactDetailModal"'))
ok('alv-modal-head' in B_NOW,
   '  wearing the house modal head')
ok('modal-fullscreen-mobile' in B_NOW,
   '  and full-screen on a phone, like the Add/Edit modal beside it')
for act in ('event', 'edit', 'delete'):
    ok('data-act="%s"' % act in B_NOW,
       '  with a %s control in the footer' % act)
ok(B_NOW.count('data-dismiss="modal"') >= 2,
   '  and a way out that is not the keyboard')
# THE FOOTER ORDER, BECAUSE THE PHONE REVERSES IT.
# .modal-footer-stack-mobile is column-reverse below 768px, so the LAST
# control in markup is the TOP one on a phone - which is why the Add/Edit
# modal beside this one puts Cancel first and Save last. Written the
# other way round, Add Event landed under Close on the phone stack.
_foot = B_NOW[B_NOW.index('id="contactDetailModal"'):]
_foot = _foot[_foot.index('modal-footer'):
              _foot.index('</div>', _foot.index('modal-footer'))]
ok(_foot.index('data-dismiss') < _foot.index('data-act="event"'),
   '  with Close FIRST in markup, so the phone stack puts Add Event on '
   'top - the footer is column-reverse below 768px')
ok('column-reverse' in NOW,
   '  which is what .modal-footer-stack-mobile does, and why')

# THE EXPAND IS GONE, all of it.
ok('toggleCardExpand' not in B_NOW,
   'the in-place expand is gone')
ok(not re.search(r'\.expanded\b', B_NOW),
   '  and no rule selects a state nothing sets')
ok("classList.add('expanded')" not in B_NOW,
   '  and nothing sets one')
ok(not APPLIED or 'toggleCardExpand' in B_WAS,
   'CONTROL: clicking a card grew it in place, until this round')
ok(not APPLIED or re.search(r'\.expanded\b', B_WAS),
   'CONTROL: and seven rules selected that state')

# THE ADD/EDIT MODAL IS UNTOUCHED - it was already a modal.
ok('id="contactModal"' in B_NOW,
   'the Add/Edit modal is still there')
if APPLIED:
    a = WAS[WAS.find('id="contactModal"'):WAS.find('id="eventModal"')]
    b = NOW[NOW.find('id="contactModal"'):NOW.find('id="eventModal"')]
    ok(a == b, '  byte for byte - this round did not touch it',
       'the Add/Edit modal changed')
else:
    skip('the Add/Edit modal is byte-identical', 'not applied')


# ==========================================================================
head('2. THE BODY IS CLONED MARKUP, NOT MARKUP BUILT IN SCRIPT')
# ==========================================================================
# CC-1 refused script-built markup on the sibling page and wrote down
# why: markup a gate can read is worth more than markup that is
# convenient to generate.
scripts = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>',
                               B_NOW, re.S))
ok(scripts.count('cloneNode(true)') >= 2,
   'the modal body is filled from clones of the card own markup',
   scripts.count('cloneNode(true)'))
ok(not re.search(r'contactDetail\w*\s*\.\s*innerHTML', scripts),
   '  and never from a string')
ok('openContactDetail' in scripts,
   'there is one function that opens it')

# THE FOOTER CLICKS THE CARD'S OWN BUTTONS.
ok('CONTACT_ACTS' in scripts,
   'the footer maps its three controls onto the card own buttons')
ok('.click()' in scripts,
   '  and clicks them rather than re-declaring what they carry')
ok('hidden.bs.modal' in scripts,
   '  after this modal has closed, so two are never open at once')
ok('btn.disabled = !src' in scripts,
   'a control with no live button behind it is disabled - which is '
   'what a contact the user may not edit draws')


# ==========================================================================
head('3. THE EMOJI GO, IN CC-1 WORDING')
# ==========================================================================
model = read(alv_tree.path_of(MODEL))
for ch in EMOJI:
    ok(ch not in B_NOW, 'no %r in the chrome' % ch)
ok(not APPLIED or any(ch in B_WAS for ch in EMOJI),
   'CONTROL: all four were there, until this round')
ok('days away' not in B_NOW,
   'the countdown no longer says "days away"')
for word in ('Today', 'Tomorrow'):
    ok(word in B_NOW and word in model,
       '"%s" is what both celebration pages say' % word)
ok(re.search(r'\{\{ days \}\} days\s*$', B_NOW, re.M)
   or '{{ days }} days' in B_NOW,
   'and "N days" - the calendar wording, taken on CC-1 decision')
ok('THE COUNTDOWN LOSES ITS EMOJI' in NOW and
   'THE COUNTDOWN LOSES ITS EMOJI' in model,
   'and both pages carry the same reason, in the same words')


# ==========================================================================
head('4. RENDERED - THE GRID STOPS MOVING')
# ==========================================================================
# THIS IS THE REQUEST. The card grew in place and pushed every card
# after it down the page. The claim is a RELATION between two renders:
# the cards below the one clicked stay where they are.
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False


def styles_of(t):
    return re.findall(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)


def scripts_of(t):
    return re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script\s*>',
                      t, re.S | re.I)


def esc(js):
    return js.replace('</script', '<\\/script')


def flatten(mk):
    """The template's own text, with Django taken out of it.

    APPLIED TO THE SCRIPTS TOO, not only the markup. The page's
    JavaScript carries template tags - a left brace and a percent sign
    is not valid JS, and the whole file fails to parse, which is why
    the first fixture reported `openContactDetail: undefined` and a
    page error reading "Unexpected token '%'"."""
    # A {% comment %} BLOCK IS NOT OUTPUT, so its TEXT must go with its
    # tags. Stripping only the tags leaves the prose on the page, which
    # Django never renders - the first fixture drew this round's own
    # note about the emoji inside every event row.
    mk = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '',
                mk, flags=re.S)
    mk = re.sub(r'\{%\s*(?:if|elif|else|endif|for|endfor|empty|with|'
                r'endwith|csrf_token|load|block|'
                r'endblock|extends)[^%]*%\}', '', mk)
    mk = re.sub(r'\{%[^%]*%\}', '', mk)
    mk = re.sub(r'\{\{[^}]*\}\}', 'X', mk)
    return re.sub(r'\{#.*?#\}', '', mk, flags=re.S)


def card_block(t):
    i = t.find('<div class="contact-card">')
    j = t.find('<!-- Events for this contact -->', i)
    k = t.find('</div>', t.find('</div>', t.find('event-notify-row', j)))
    end = t.find('\n        </div>', j)
    return t[i:end + len('\n        </div>')]


def modal_block(t, mid):
    i = t.find('<div class="modal fade" id="%s"' % mid)
    if i < 0:
        return ''
    depth, j = 0, i
    while j < len(t):
        if t.startswith('<div', j):
            depth += 1
        elif t.startswith('</div>', j):
            depth -= 1
            if depth == 0:
                return t[i:j + 6]
        j += 1
    return ''


def fixture(src, name):
    card = flatten(card_block(src))
    grid = ''.join(
        card.replace('>X<', '>Contact %d<', 1) % n if '>X<' in card
        else card for n in (1, 2, 3))
    grid = ''
    for n in (1, 2, 3):
        one = card.replace('class="contact-name">X<',
                           'class="contact-name">Contact %d<' % n)
        grid += one
    mods = (flatten(modal_block(src, 'contactDetailModal'))
            + flatten(modal_block(src, 'contactModal')))
    # THE TOGGLE BUTTON, because toggleView() reads it unguarded and
    # the fixture is now required to call toggleView() rather than
    # imitate it. CC-3, 17 Oct 2026.
    body = ('<div class="main-content with-sidebar"><div class="container">'
            '<button id="viewToggleBtn"></button>'
            '<div class="contacts-container">%s</div></div>%s</div>'
            % (grid, mods))
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s</head>'
            '<body>%s<script>%s</script><script>%s</script>%s</body></html>'
            % (read(BOOT) + (
                   # THE SCROLLBAR IS ALWAYS THERE, ON PURPOSE.
                   # Bootstrap puts `modal-open` on the body when a
                   # modal opens, which hides the page scrollbar - the
                   # container gets ~15px wider and every card reflows
                   # by about 11px. That is real, it moves the whole
                   # grid together, and it has nothing to do with one
                   # card pushing the next. Forcing the scrollbar to
                   # stay removes the confound instead of weakening the
                   # claim to work around it.
                   '\nhtml { overflow-y: scroll; }\n'),
               '\n'.join(styles_of(read(
                alv_tree.path_of('base.html')))),
               ''.join('<style>%s</style>' % c for c in styles_of(src)),
               body, esc(read(JQ)), esc(read(BSJS)),
               ''.join('<script>%s</script>' % esc(flatten(s))
                       for s in scripts_of(src))))
    p = os.path.join(SCRATCH, name)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(html)
    return p


LOOK = """() => {
  const cards = [...document.querySelectorAll('.contact-card')];
  const m = document.getElementById('contactDetailModal');
  const r = e => Math.round(e.getBoundingClientRect().top);
  return {tops: cards.map(r),
          heights: cards.map(e => Math.round(
              e.getBoundingClientRect().height)),
          modalShown: !!(m && m.classList.contains('show')
                         && getComputedStyle(m).display === 'block'),
          title: m ? m.querySelector('.modal-title').textContent.trim()
                   : '',
          bodyEvents: m ? m.querySelectorAll('.event-item').length : 0,
          bodyDetails: m ? m.querySelectorAll('.contact-details').length
                         : 0,
          // CC-3: PIXELS, NOT NODES. The defect that shipped was an
          // event list present and invisible, which a count cannot
          // tell from one that works.
          bodyEventH: (() => {
              const e = m && m.querySelector('.modal-body .event-list');
              return e ? Math.round(e.getBoundingClientRect().height) : 0;
          })(),
          cardEventH: (() => {
              const e = cards[0] && cards[0].querySelector('.event-list');
              return e ? Math.round(e.getBoundingClientRect().height) : 0;
          })(),
          bodyCtl: m ? m.querySelectorAll(
              '.modal-body button.icon-action-btn,'
              + ' .modal-body input.notify-checkbox').length : 0,
          bodyInline: m ? m.querySelectorAll(
              '.modal-body [onclick], .modal-body [onchange]').length : 0};
}"""

if not have_pw or not all(os.path.isfile(f) for f in (BOOT, JQ, BSJS)):
    skip('the grid in a browser', 'playwright or a fixture is missing')
else:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def shot(src, name, compact=True, click=True):
            ctx = br.new_context(viewport={'width': 1280, 'height': 900})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            _goto(pg, fixture(src, name))
            pg.wait_for_timeout(150)
            if compact:
                # THE PAGE'S OWN FUNCTION, NOT AN IMITATION OF IT.
                # CC-3, 17 Oct 2026. Adding the class is half of what
                # toggleView does; the other half is an inline
                # display:none on the event list, and that is the half
                # cloneNode copied into an empty modal on the live
                # site. A fixture that simulates a state can only find
                # faults in the part it simulated.
                _toggled = pg.evaluate("""() => {
                    if (typeof toggleView === 'function') {
                        toggleView();
                        return true;
                    }
                    document.querySelectorAll('.contact-card').forEach(
                        c => c.classList.add('compact-view'));
                    return false;
                }""")
                if not _toggled:
                    print('     !! toggleView was not callable - the '
                          'fixture fell back to adding the class, and '
                          'the inline hide is NOT in play')
                pg.wait_for_timeout(60)
            before = pg.evaluate(LOOK)
            if click:
                try:
                    pg.evaluate("""() => {
                        const c = document.querySelectorAll(
                            '.contact-card')[0];
                        if (typeof openContactDetail === 'function') {
                            openContactDetail(c);
                        } else if (typeof toggleCardExpand === 'function') {
                            toggleCardExpand(c);
                        }
                    }""")
                except Exception:
                    pass
                pg.wait_for_timeout(500)
            after = pg.evaluate(LOOK)
            ctx.close()
            return before, after

        # CC-3's CONTROL - CC-2's PAGE, MEASURED THE SAME WAY.
        # A round that fixes an invisible body has to show the body
        # invisible before it. This reads the page as CC-2 left it,
        # which is CC-3's own backup, and renders it in the same
        # fixture. 0px there and a positive number below is the whole
        # defect and the whole fix, in two numbers.
        _c3 = PATH + '.bak_contactwire'
        if os.path.isfile(_c3):
            _, c3 = shot(read(_c3), 'cc3_was.html')
            ok(c3['modalShown'],
               'CONTROL: CC-2 opened the modal correctly')
            ok(c3['bodyEvents'] >= 1,
               '  CONTROL: and the event list really was in the body')
            ok(c3['bodyEventH'] == 0,
               '  CONTROL: and it was 0px tall - present, and invisible, '
               'which is what he saw', '%dpx' % c3['bodyEventH'])
            ok(c3['bodyInline'] > 0,
               '  CONTROL: and every copied control still carried its '
               'inline handler', c3['bodyInline'])
        else:
            skip('CC-2 measured the same way', 'CC-3 is not applied')

        n_before, n_after = shot(NOW, 'cc2_now.html')
        ok(len(n_before['tops']) == 3,
           'three contact cards are drawn', n_before['tops'])
        ok(n_after['modalShown'],
           'clicking the first card OPENS the modal')
        ok(n_after['title'].startswith('Contact 1'),
           '  titled with that contact name: %r' % n_after['title'])
        ok(n_after['bodyDetails'] >= 1,
           '  carrying the contact details', n_after['bodyDetails'])
        ok(n_after['bodyEvents'] >= 1,
           '  and the event list', n_after['bodyEvents'])
        # ---- CC-3, 17 Oct 2026 - MEASURED, NOT COUNTED ---------------
        # He opened a contact on alivente.online and got a header, a
        # footer and nothing between them. The list was in the body the
        # whole time, carrying the inline display:none that
        # toggleView() had written on the card's copy of it.
        ok(n_after['bodyEventH'] > 0,
           '  and it is VISIBLE, not merely present - %dpx of event '
           'list in the body' % n_after['bodyEventH'],
           '%dpx' % n_after['bodyEventH'])
        ok(n_after['cardEventH'] == 0,
           '  while the card behind it stays compact - the inline hide '
           'was cleared on the COPY, not on the card',
           '%dpx' % n_after['cardEventH'])
        ok(n_after['bodyCtl'] > 0,
           '  the copy brings the event controls with it',
           n_after['bodyCtl'])
        ok(n_after['bodyInline'] == 0,
           '  and not one of them kept an inline handler, so no copied '
           'pencil opens a second modal and no copied checkbox posts '
           'on its own', n_after['bodyInline'])
        # ---- AND IT DRIVES THE CARD'S OWN CONTROL --------------------
        # The check above is the inverse of the implementation - it
        # would pass just as well against a copy whose controls do
        # NOTHING. So the copy is clicked for real, and the questions
        # are whether the CARD's button fired and whether this modal
        # got out of the way first, which is the whole contract CC-2
        # wrote down and never tested.
        _ctx = br.new_context(viewport={'width': 1280, 'height': 900})
        _ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        _pg = _ctx.new_page()
        _goto(_pg, fixture(NOW, 'cc3_drive.html'))
        _pg.wait_for_timeout(150)
        _pg.evaluate("() => { if (typeof toggleView === 'function') "
                     "{ toggleView(); } }")
        _pg.wait_for_timeout(60)
        _pg.evaluate("""() => {
            const c = document.querySelectorAll('.contact-card')[0];
            window.__hit = 0;
            c.querySelectorAll('.event-list button').forEach(
                b => b.addEventListener('click',
                                        () => { window.__hit++; }));
            if (typeof openContactDetail === 'function') {
                openContactDetail(c);
            }
        }""")
        _pg.wait_for_timeout(500)
        _drive = _pg.evaluate("""() => {
            const b = document.querySelector(
                '#contactDetailModal .modal-body .event-list button');
            if (!b) { return {found: false}; }
            try { b.click(); } catch (e) { }
            return {found: true};
        }""")
        _pg.wait_for_timeout(900)
        _out = _pg.evaluate("""() => {
            const m = document.getElementById('contactDetailModal');
            return {hit: window.__hit || 0,
                    shown: !!(m && m.classList.contains('show')
                              && getComputedStyle(m).display === 'block')};
        }""")
        _ctx.close()
        ok(_drive.get('found'),
           '  a copied event control is there to be clicked')
        ok(_out['hit'] == 1,
           '  and clicking it fires the CARD own button exactly once, '
           'not a dead handler on the copy', _out['hit'])
        ok(not _out['shown'],
           '  with this modal closed first, so two are never open at '
           'once', _out['shown'])
        # THE GAPS, NOT THE TOPS.
        #
        # Opening a Bootstrap modal puts `modal-open` on the body, which
        # hides the page scrollbar - the container gets ~15px wider and
        # every card reflows by about 11px. That is the modal doing what
        # modals do, and it moves the whole grid together. What the
        # request is about is one card pushing the NEXT one down, so the
        # claim is the DISTANCE between consecutive cards, which the
        # scrollbar cannot touch.
        def gaps(r):
            return [r['tops'][i + 1] - r['tops'][i]
                    for i in range(len(r['tops']) - 1)]

        # WHAT THE REQUEST IS ABOUT, AND WHAT IT IS NOT.
        #
        # Opening a Bootstrap modal puts `modal-open` on the body AND
        # pads it by the scrollbar width, so the content column narrows
        # by about 15px and every card reflows a little. That is the
        # modal doing what modals do: it moves the whole grid together
        # and it is not one card pushing the next.
        #
        # The request was that a card stop growing and shoving the rest
        # of the grid down. Stated as relations WITHIN a render, which
        # neither the scrollbar nor the body padding can touch: every
        # gap is the same, and the card that was clicked is no taller
        # than the ones that were not.
        print('      tops before %s   after %s'
              % (n_before['tops'], n_after['tops']))
        print('      gaps before %s   after %s'
              % (gaps(n_before), gaps(n_after)))
        ok(max(gaps(n_after)) - min(gaps(n_after)) <= 2,
           'AND THE CARD DOES NOT PUSH THE ONE BELOW IT: every gap is '
           'the same, %s' % gaps(n_after))
        ok(max(n_after['heights']) - min(n_after['heights']) <= 2,
           '  because the clicked card is no taller than its '
           'neighbours: %s' % n_after['heights'])
        # CC-3: AND NOT TALLER THAN IT WAS, EITHER. In the real compact
        # grid the three cards share a row, so "the one below" is a
        # card that does not exist and every gap is 0 whatever happens.
        # The claim that survives the grid is that the click changed no
        # card's height at all.
        _grew = [a - b for a, b in zip(n_after['heights'],
                                       n_before['heights'])]
        ok(max(_grew) <= 2,
           '  and no taller than it was BEFORE the click either - the '
           'row did not move: %s' % n_after['heights'], _grew)

        if APPLIED:
            w_before, w_after = shot(WAS, 'cc2_was.html')
            # CC-3, 17 Oct 2026 - RE-STATED FOR THE ROW.
            # These two asked whether the clicked card pushed the card
            # BELOW it down, which was the right question against a
            # fixture that stacked the cards in a column. The fixture
            # calls the page's own toggleView now, so the container is
            # the three-across .compact-grid the page really draws, and
            # there is no card below - the clicked card grew the whole
            # ROW. Measured: 48px each before the click, 611px each
            # after. That is the defect, and it is worse than the one
            # the old wording described.
            _was_grew = [a - b for a, b in zip(w_after['heights'],
                                               w_before['heights'])]
            ok(min(_was_grew) > 20,
               'CONTROL: before this round the click grew the card from '
               '%dpx to %dpx' % (w_before['heights'][0],
                                 w_after['heights'][0]),
               'if it did not, this round is aimed at nothing')
            ok(len(_was_grew) > 1 and min(_was_grew[1:]) > 20,
               '  AND DRAGGED ITS NEIGHBOURS WITH IT - nobody clicked '
               'those two, and they grew by %s' % _was_grew[1:])
            ok(max(gaps(w_before)) - min(gaps(w_before)) <= 2,
               '  while before the click they WERE the same: %s'
               % gaps(w_before))
            ok(not w_after['modalShown'],
               '  and no modal opened')
        else:
            skip('CONTROL: the cards below used to move', 'not applied')
        br.close()


# ==========================================================================
head('5. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(SUFFIX in _r and '.bak_gatespeed' in _r
       and _r.index(SUFFIX) > _r.index('.bak_gatespeed'),
       '  and sits after .bak_gatespeed', _r[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s runs this suite' % PS1)
ok("Text = 'contactDetailModal'" in ps1,
   'and holds a sentinel on the modal')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

bad = [i + 1 for i, ln in enumerate(NOW.split('\n'))
       if ln.count('{#') != ln.count('#}')]
ok(not bad, 'every {# comment on the page closes on its own line', bad)

wd = as_cc2_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when CC-2 left it'
   % CONVERTED_NOW)
co = as_cc2_left('test_code_only.py')
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
    print('  Clicking a contact in the compact view opened it in place,')
    print('  growing the card and pushing every card after it down the')
    print('  grid. It opens in a modal now, filled with clones of the')
    print('  card own markup, and the emoji countdowns take the wording')
    print('  CC-1 gave the calendar two days ago.')
sys.exit(1 if failed else 0)
