# -*- coding: utf-8 -*-
"""apply_contact_wire.py - round CC-3, 17 Oct 2026.

CC-2 SHIPPED A MODAL THAT COULD NEVER SHOW ANYTHING.

Demetri, 17 Oct, two screenshots of alivente.online: the contact modal
opens with the right name, the right Family tag and the right four
buttons - and nothing at all between them.

THE CAUSE, IN THREE LINES THAT ARE EACH CORRECT ALONE.

    toggleView() hides the event list with an INLINE style:

        eventList.style.display = 'none';

    CC-2 fills the modal with cloneNode(true), WHICH COPIES INLINE
    STYLES, so the clone arrives still carrying display:none.

    The rule CC-2 wrote to show it inside the modal sets max-height
    and overflow. It never sets display, and an author-level rule
    cannot beat an inline style in any case.

And CC-2's own comment says, in the file:

    "they are the same elements the card draws, outside .compact-view,
     which is why the rules that hide them in a compact card do not
     reach them"

That is true of the CLASS rule - `.contact-card.compact-view
.contact-details { display: none !important }` really does stop
matching once the node is cloned out. It is false of the INLINE style,
which travels with the node. One sentence, right about one of the two
mechanisms, and the one it was wrong about is the one that mattered.

WHY THE SUITE DID NOT CATCH IT. Two reasons, both worth fixing:

    ITS FIXTURE PUT THE PAGE INTO COMPACT VIEW BY ADDING THE CLASS,
    not by calling toggleView(). The class is half of what the real
    page does; the inline style is the other half, and the half the
    fixture skipped is the half that broke. A fixture that simulates
    the state instead of entering it can only find faults in the
    half it simulated.

    IT COUNTED NODES, NOT PIXELS. `bodyEvents >= 1` is satisfied by
    an event list that is present and invisible. This round asks for
    its HEIGHT.

WHAT THIS ROUND DOES

    The clone is shown: the inline display the card put on it is
    cleared on the copy, and only on the copy.

    EVERY CONTROL IN THE COPY IS A COPY, AND IS WIRED TO ITS ORIGINAL.
    Once the list is actually visible it brings each event's pencil and
    bin and five notification checkboxes with it. Left alone they are
    live-looking and wrong: the pencil's inline onclick would open the
    event editor ON TOP of this modal, which CC-2 forbids in writing,
    and a cloned checkbox would post a change to the server and leave
    the card's own checkbox showing the opposite. So each copied
    control is paired with the original it was copied from - by index,
    which a deep clone guarantees - and does what the footer does:
    a button closes this modal and clicks the card's button; a
    checkbox forwards its new state to the card's checkbox, so exactly
    one checkbox is ever the real one.

WHAT IT DOES NOT DO: change any rule in the stylesheet. Adding
`display: block` beside the max-height would also have made the body
appear, and would have left the inline style on the node and the
mechanism unexplained. The fault is a copied inline style; the fix is
to stop copying it.
"""
import os
import sys

SUFFIX = '.bak_contactwire'
PAGE = 'pages/templates/celebration_management.html'
SUITE = 'test_contact_modal.py'
PATCHER = 'apply_contact_wire.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS = 'alv_rounds.py'
CHECK = False

# -------------------------------------------------------- 1. the prose
NOTE_WAS = """/* CC-2, 17 Oct 2026 - THE CONTACT DETAIL MODAL.
   The body holds clones of the card's own .contact-details and
   .event-list, so nothing here restyles them - they are the same
   elements the card draws, outside .compact-view, which is why the
   rules that hide them in a compact card do not reach them. */"""
NOTE_NOW = """/* CC-2, 17 Oct 2026 - THE CONTACT DETAIL MODAL.
   The body holds clones of the card's own .contact-details and
   .event-list, so nothing here restyles them - they are the same
   elements the card draws.

   CC-3, 17 Oct 2026 - AND THE SENTENCE THAT USED TO FINISH THAT
   PARAGRAPH WAS WRONG, which is why the modal shipped empty. It said
   the rules hiding a compact card's details do not reach the clone.
   True of the CLASS rule below, which stops matching once the node is
   outside .contact-card.compact-view. FALSE of the INLINE style
   toggleView() writes on the event list, which cloneNode copies onto
   the copy, and which no rule here can beat. The copy has that style
   cleared in script now; nothing below tries to out-specify it. */"""

# ------------------------------------------------------- 2. the filler
FILL_WAS = """    const body = el.querySelector('.modal-body');
    while (body.firstChild) { body.removeChild(body.firstChild); }
    card.querySelectorAll('.contact-details').forEach(function (n) {
        body.appendChild(n.cloneNode(true));
    });
    const events = card.querySelector('.event-list');
    if (events) { body.appendChild(events.cloneNode(true)); }"""
FILL_NOW = """    const body = el.querySelector('.modal-body');
    while (body.firstChild) { body.removeChild(body.firstChild); }
    card.querySelectorAll('.contact-details').forEach(function (n) {
        copyInto(n, body);
    });
    const events = card.querySelector('.event-list');
    if (events) { copyInto(events, body); }"""

# ------------------------------------------------------ 3. the helpers
HELP_WAS = """function openContactDetail(card) {"""
HELP_NOW = """// CC-3, 17 Oct 2026 - A COPY THAT CAN BE SEEN, AND WHOSE CONTROLS ARE
// NOT DEAD.
//
// toggleView() hides the event list with an INLINE style, and
// cloneNode(true) copies inline styles, so CC-2's clone arrived still
// carrying display:none and the modal opened empty on the live site.
// The copy gets that one property cleared - on the copy, never on the
// card, which still needs it to stay compact behind the modal.
//
// AND EVERY CONTROL IN THE COPY IS A COPY. A copied pencil still
// carries its inline onclick, which would open the event editor on top
// of this modal - CC-2 forbids two modals at once in writing. A copied
// checkbox would post to the server and leave the card's own checkbox
// showing the opposite. So each one is paired with the original it was
// copied from. The pairing is BY INDEX over the same selector run on
// the source node and on its own deep clone, which is the one case
// where index pairing is exact rather than hopeful: the clone has the
// same elements in the same order by definition.
//
// THE SELECTOR NAMES THE PROPERTY, NOT THE CLASSES. The first spelling
// listed the two classes the event row uses - and missed the MOBILE
// action bar inside the same row, whose buttons carry the same two
// inline handlers under a third class. A list of classes goes stale
// the first time somebody adds a fourth. What actually makes a copied
// control dangerous is that it carries an inline handler, so that is
// what is asked for.
const CLONE_WIRE = '[onclick], [onchange]';

function wireCopy(copy, real) {
    copy.removeAttribute('onclick');
    copy.removeAttribute('onchange');
    copy.onclick = null;
    copy.onchange = null;
    if (copy.tagName === 'INPUT') {
        copy.addEventListener('change', function () {
            // THE CARD'S CHECKBOX IS THE REAL ONE. Its own onchange
            // calls updateNotification, so the save happens once, from
            // the control that will still be on the page afterwards.
            real.checked = copy.checked;
            real.dispatchEvent(new Event('change', {bubbles: true}));
        });
    } else {
        copy.addEventListener('click', function (e) {
            e.preventDefault();
            contactDetailPending = real;
            $(contactDetailEl()).modal('hide');
        });
    }
}

function copyInto(node, body) {
    const copy = node.cloneNode(true);
    copy.style.display = '';
    const mine = copy.querySelectorAll(CLONE_WIRE);
    const real = node.querySelectorAll(CLONE_WIRE);
    for (let i = 0; i < mine.length && i < real.length; i++) {
        wireCopy(mine[i], real[i]);
    }
    body.appendChild(copy);
    return copy;
}

function openContactDetail(card) {"""

# ------------------------------------------------------ 4. the register
REG_WAS = """    # AR-1, 17 Oct 2026 - a suite that died is not a suite that
    # disagreed; the first is re-run alone, the second is not.
    '.bak_autoretry',
]"""
REG_NOW = """    # AR-1, 17 Oct 2026 - a suite that died is not a suite that
    # disagreed; the first is re-run alone, the second is not.
    '.bak_autoretry',
    # CC-3, 17 Oct 2026 - CC-2's modal opened empty on the live site:
    # cloneNode copies the inline style toggleView writes.
    '.bak_contactwire',
]"""

# ------------------------------------------------------ 5. the sentinel
SENT_WAS = (
    "    @{ File = 'alv_run.py'; Text = 'died.append'; "
    "What = 'AR-1: a suite that printed no tally is re-run once, "
    "alone' },")
SENT_NOW = SENT_WAS + """
    # ------------------------------------------------- CC-3, 17 Oct 2026
    @{ File = 'pages\\templates\\celebration_management.html'; Text = 'copyInto'; What = 'CC-3: the copy is shown and its controls are wired' },"""


# ------------------------------------------------- 6. the fixture half
# THE FIXTURE ENTERED COMPACT VIEW BY ADDING THE CLASS. The page enters
# it by calling toggleView(), which adds the class AND writes the
# inline hide. The fixture simulated half the state, and the half it
# left out is the half that broke. It calls the page's own function
# now - which needs the toggle button the page has, so the fixture
# grows one.
FIXB_WAS = """    body = ('<div class="main-content with-sidebar"><div class="container">'
            '<div class="contacts-container">%s</div></div>%s</div>'
            % (grid, mods))"""
FIXB_NOW = """    # THE TOGGLE BUTTON, because toggleView() reads it unguarded and
    # the fixture is now required to call toggleView() rather than
    # imitate it. CC-3, 17 Oct 2026.
    body = ('<div class="main-content with-sidebar"><div class="container">'
            '<button id="viewToggleBtn"></button>'
            '<div class="contacts-container">%s</div></div>%s</div>'
            % (grid, mods))"""

COMPACT_WAS = """            if compact:
                pg.evaluate(\"\"\"() => {
                    document.querySelectorAll('.contact-card').forEach(
                        c => c.classList.add('compact-view'));
                }\"\"\")
                pg.wait_for_timeout(60)"""
COMPACT_NOW = """            if compact:
                # THE PAGE'S OWN FUNCTION, NOT AN IMITATION OF IT.
                # CC-3, 17 Oct 2026. Adding the class is half of what
                # toggleView does; the other half is an inline
                # display:none on the event list, and that is the half
                # cloneNode copied into an empty modal on the live
                # site. A fixture that simulates a state can only find
                # faults in the part it simulated.
                _toggled = pg.evaluate(\"\"\"() => {
                    if (typeof toggleView === 'function') {
                        toggleView();
                        return true;
                    }
                    document.querySelectorAll('.contact-card').forEach(
                        c => c.classList.add('compact-view'));
                    return false;
                }\"\"\")
                if not _toggled:
                    print('     !! toggleView was not callable - the '
                          'fixture fell back to adding the class, and '
                          'the inline hide is NOT in play')
                pg.wait_for_timeout(60)"""

LOOK_WAS = """          bodyDetails: m ? m.querySelectorAll('.contact-details').length
                         : 0};
}\"\"\""""
LOOK_NOW = """          bodyDetails: m ? m.querySelectorAll('.contact-details').length
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
}\"\"\""""

CHK_WAS = """        ok(n_after['bodyEvents'] >= 1,
           '  and the event list', n_after['bodyEvents'])"""
CHK_NOW = """        ok(n_after['bodyEvents'] >= 1,
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
        _pg.evaluate(\"\"\"() => {
            const c = document.querySelectorAll('.contact-card')[0];
            window.__hit = 0;
            c.querySelectorAll('.event-list button').forEach(
                b => b.addEventListener('click',
                                        () => { window.__hit++; }));
            if (typeof openContactDetail === 'function') {
                openContactDetail(c);
            }
        }\"\"\")
        _pg.wait_for_timeout(500)
        _drive = _pg.evaluate(\"\"\"() => {
            const b = document.querySelector(
                '#contactDetailModal .modal-body .event-list button');
            if (!b) { return {found: false}; }
            try { b.click(); } catch (e) { }
            return {found: true};
        }\"\"\")
        _pg.wait_for_timeout(900)
        _out = _pg.evaluate(\"\"\"() => {
            const m = document.getElementById('contactDetailModal');
            return {hit: window.__hit || 0,
                    shown: !!(m && m.classList.contains('show')
                              && getComputedStyle(m).display === 'block')};
        }\"\"\")
        _ctx.close()
        ok(_drive.get('found'),
           '  a copied event control is there to be clicked')
        ok(_out['hit'] == 1,
           '  and clicking it fires the CARD own button exactly once, '
           'not a dead handler on the copy', _out['hit'])
        ok(not _out['shown'],
           '  with this modal closed first, so two are never open at '
           'once', _out['shown'])"""

# AND THE CONTROL: the same measurement against CC-2's own page.
# ----------------------------------- 7. the grid claims, re-stated
# THE FIXTURE CALLS toggleView() NOW, so the container really becomes
# .compact-grid - three cards across one row, which is what the page
# has done since 29 Sep. CC-2's two claims were written against a
# fixture that left the container a single column, where "the card
# below" existed. In a row there is no card below; what the old expand
# did was grow the WHOLE ROW, neighbours and all. Measured: 48px each
# before the click, 611px each after.
#
# So the claims are re-stated to say what the render can show, and the
# CONTROL is re-stated to the defect as it actually looked. Neither is
# weakened - the control still fails if the old behaviour is absent.
GRID_WAS = """        ok(max(gaps(n_after)) - min(gaps(n_after)) <= 2,
           'AND THE CARD DOES NOT PUSH THE ONE BELOW IT: every gap is '
           'the same, %s' % gaps(n_after))
        ok(max(n_after['heights']) - min(n_after['heights']) <= 2,
           '  because the clicked card is no taller than its '
           'neighbours: %s' % n_after['heights'])"""
GRID_NOW = """        ok(max(gaps(n_after)) - min(gaps(n_after)) <= 2,
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
           'row did not move: %s' % n_after['heights'], _grew)"""

CTRL2_WAS = """            ok(max(gaps(w_after)) - min(gaps(w_after)) > 2,
               'CONTROL: before this round the gaps were NOT the same - '
               '%s - because the clicked card pushed the next one down'
               % gaps(w_after),
               'if they were, this round is aimed at nothing')
            ok(w_after['heights'][0] > w_after['heights'][1],
               '  and it grew past its neighbours: %d against %d'
               % (w_after['heights'][0], w_after['heights'][1]))"""
CTRL2_NOW = """            # CC-3, 17 Oct 2026 - RE-STATED FOR THE ROW.
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
               'those two, and they grew by %s' % _was_grew[1:])"""

CTRL_WAS = """        n_before, n_after = shot(NOW, 'cc2_now.html')"""
CTRL_NOW = """        # CC-3's CONTROL - CC-2's PAGE, MEASURED THE SAME WAY.
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

        n_before, n_after = shot(NOW, 'cc2_now.html')"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('CC-3 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pg = os.path.join(root, PAGE.replace('/', os.sep))
    t = read(pg)

    # ---------------------------------------------------------------- 0
    if 'function copyInto(' in t:
        print('CC-3  already applied - the copy is shown and wired.')
        return 0

    # ---------------------------------------------------------------- 1
    # CC-2 MUST BE THERE. This round corrects it and would otherwise be
    # writing a helper nothing calls.
    if 'openContactDetail' not in t:
        refuse('%s has no contact detail modal - CC-2 is not applied'
               % PAGE)
    # AND THE FAULT MUST STILL BE THERE. The inline hide is what this
    # round exists to stop copying; if toggleView has stopped writing
    # it, the whole reasoning above has moved and the round should be
    # re-thought rather than applied.
    if "eventList.style.display = 'none'" not in t:
        refuse('toggleView no longer writes the inline hide this round '
               'is about - re-measure before applying')

    t = swap(t, NOTE_WAS, NOTE_NOW, '%s (the CC-2 note)' % PAGE)
    t = swap(t, HELP_WAS, HELP_NOW, '%s (the copy helpers)' % PAGE)
    t = swap(t, FILL_WAS, FILL_NOW, '%s (the body fill)' % PAGE)
    # AND THE TWO RAW CLONES IN THE BODY FILL ARE GONE - NAMED EXACTLY.
    # The first spelling of this gate asked whether 'cloneNode(true));'
    # appeared anywhere after the new helper, and refused: the badge
    # beside the title is cloned that way too, legitimately, and has
    # been since CC-2. A gate must name the call it means.
    for dead in ('body.appendChild(n.cloneNode(true));',
                 'body.appendChild(events.cloneNode(true));'):
        if dead in t:
            refuse('a raw clone survives in the body fill: %r' % dead)
    out[pg] = t

    # ---------------------------------------------------------------- 2
    # THE SUITE THAT LET IT THROUGH. Two faults, both in how it looked
    # rather than in what it claimed: it imitated compact view instead
    # of entering it, and it counted nodes where it meant pixels.
    p = os.path.join(root, SUITE)
    s = read(p)
    # A HALF-APPLIED DETECTOR, NOT A GATE ON THE TREE. check_gates.py
    # flags this - it requires a string absent that this round writes -
    # and it is right to, because that shape is nearly always the bug.
    # Here it is the step-0 check for the second file: the page half
    # has already been found unapplied above, so finding the suite half
    # applied means a previous run died between the two writes, and
    # swapping again would refuse on a missing anchor with a worse
    # message than this one.
    if 'bodyEventH' in s:
        refuse('%s already measures the height but the page does not '
               'have copyInto - a previous run stopped between the two. '
               'Restore both from %s and apply again.' % (SUITE, SUFFIX))
    s = swap(s, FIXB_WAS, FIXB_NOW, '%s (the fixture body)' % SUITE)
    s = swap(s, COMPACT_WAS, COMPACT_NOW, '%s (entering compact view)'
             % SUITE)
    s = swap(s, LOOK_WAS, LOOK_NOW, '%s (the probe)' % SUITE)
    s = swap(s, CTRL_WAS, CTRL_NOW, '%s (the control)' % SUITE)
    s = swap(s, CHK_WAS, CHK_NOW, '%s (the measured checks)' % SUITE)
    s = swap(s, GRID_WAS, GRID_NOW, '%s (the grid claim)' % SUITE)
    s = swap(s, CTRL2_WAS, CTRL2_NOW, '%s (the grid control)' % SUITE)
    import ast
    try:
        ast.parse(s)
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (SUITE, e.lineno, e.msg))
    out[p] = s

    # ---------------------------------------------------------------- 3
    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), REG_WAS, REG_NOW, '%s (ROUNDS)' % ROUNDS)

    # ---------------------------------------------------------------- 3
    p = os.path.join(root, PS1)
    out[p] = swap(read(p), SENT_WAS, SENT_NOW, '%s (the sentinel)' % PS1)

    # ---------------------------------------------------------------- 4
    if CHECK:
        print('CC-3 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('CC-3 applied.')
    print('   the copy is shown - the inline hide is cleared on the copy')
    print('   each copied button closes the modal and clicks the card one')
    print('   each copied checkbox forwards to the card one')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
