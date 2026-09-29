# -*- coding: utf-8 -*-
"""SECTION M, ROUND M1 - THE MESSAGE BAR SAYS WHAT HAPPENED

Agreed with Demetri on 28 Sep and measured again today. A message bar
takes its colour from the message's TAG: green for a success, red for a
failure, amber for a caution, the accent for information.

WHAT IS THERE NOW - 77 message loops, in SIXTEEN different shapes.

    55  alert-secondary, a neutral grey, whatever the message said
     8  a hand-rolled {% if 'success' in tags %}...{% elif 'error' %}
     4  the same, with a different else branch
     2  alert-{{ tags }}  - which is BROKEN TODAY, see below
     7  nine further one-offs

The de facto standard is a grey bar that reports a deleted record and a
failed save in exactly the same colour.

THE TRAP, AND IT IS WHY THIS ROUND HAS A PRECONDITION.
    Django's tag for an error is the string 'error'. Bootstrap 4.1.3
    defines alert-danger and has NO alert-error at all. So
    `alert-{{ message.tags }}` renders an unstyled box for every error -
    and two pages are doing exactly that today, on the most common
    message in the system: 281 messages.error(...) calls against 158
    successes.

    Four pages already work around it by hand, each with its own
    {% if message.tags == 'error' %}. That is the symptom.

    The fix is one line in settings.py:

        MESSAGE_TAGS = {message_constants.ERROR: 'danger'}

    With it, 'error' renders as alert-danger everywhere and one shape is
    safe tree-wide. WITHOUT IT THIS ROUND MUST NOT SHIP, so the patcher
    writes settings.py FIRST and refuses if it cannot.

EXPECT MORE RED THAN THERE IS TODAY. Errors outnumber successes 281 to
158, so a lot of bars that are grey now will be red. That is the point -
a failure should look like one - and it is why this went out with a
rendered before/after sheet.

AUTO-DISMISS, DECIDED 29 SEP. Fifty-one pages carry an identical nine-line
script INSIDE the message loop that removes every bar after two seconds -
errors included. With the colour change that would mean a red bar
vanishing before it can be read, so: SUCCESS AND INFO FADE, DANGER AND
WARNING STAY until dismissed. The 51 copies go, and base carries one
implementation, because 51 copies of a rule is 51 places for it to
disagree with itself.

<center> GOES WITH THEM, and the centring does not. Fifty-odd bars centre
their text with a <center> tag - deprecated, and the thing the G-series
is removing. The text stays centred, by a rule in base on .alv-message.
The only thing that moves on the screen is the colour.

Backups: .bak_msgbar. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_msgbar'
CRLF = {}

SETTINGS = os.path.join('mysite', 'settings.py')
BASE = 'base.html'
CAL = 'celebration_calendar.html'


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('M1: %s is not a byte copy' % bak)


def swap(text, path, was, now, what, label):
    a = eol(path, was)
    if text.count(a) != 1:
        raise SystemExit('M1: %s - %s is there %d time(s), not 1'
                         % (label, what, text.count(a)))
    print('     %s' % what)
    return text.replace(a, eol(path, now), 1)


# ==========================================================================
# THE PRECONDITION
# ==========================================================================
SET_WAS = 'LANGUAGE_CODE = "en-us"'

SET_NOW = '''# THE MESSAGE TAG THAT HAS NO BOOTSTRAP CLASS - added 29 Sep 2026.
#     Django tags an error message 'error'. Bootstrap 4.1.3 defines
#     alert-danger and has no alert-error at all, so a template writing
#     `alert-{{ message.tags }}` produces an unstyled box for every
#     error - and errors are the most common message in this system:
#     281 messages.error(...) calls against 158 successes.
#
#     Two pages were doing exactly that. Four more worked around it by
#     hand, each with its own {% if message.tags == 'error' %}. This one
#     line replaces all six workarounds and lets every message bar in
#     the tree use one shape.
#                                                 [test_message_bar.py]
from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {message_constants.ERROR: 'danger'}

LANGUAGE_CODE = "en-us"'''

# ==========================================================================
# THE ONE SHAPE
# ==========================================================================
BAR = '''{%% for %(v)s in messages %%}
%(i)s  <div class="alert alert-{{ %(v)s.tags }} alert-dismissible fade show alv-message" role="alert">
%(i)s    {{ %(v)s }}
%(i)s    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
%(i)s      <span aria-hidden="true">&times;</span>
%(i)s    </button>
%(i)s  </div>
%(i)s{%% endfor %%}'''


def loops(t):
    """Every {% for X in messages %} ... {% endfor %} block, with the
    column its `for` starts at."""
    out = []
    for m in re.finditer(r'\{%\s*for\s+(\w+)\s+in\s+messages\s*%\}', t):
        depth, i = 1, m.end()
        while depth:
            nxt = re.search(r'\{%\s*(for|endfor)\b', t[i:])
            if not nxt:
                raise SystemExit('M1: a messages loop never closes')
            depth += 1 if nxt.group(1) == 'for' else -1
            i += nxt.end()
        # AND THE TAG'S OWN CLOSE. The match ends at `{% endfor`, not at
        # the `%}` after it, so a slice taken here stopped one token
        # short and left an orphan `%}` behind on all 77 pages.
        # test_button_reach.py found it by counting `{%` against `%}` -
        # which is exactly the kind of blunt check that earns its keep.
        close = t.find('%}', i)
        if close < 0:
            raise SystemExit('M1: an endfor never closes')
        i = close + 2
        j = t.rfind('\n', 0, m.start())
        indent = t[j + 1:m.start()]
        if indent.strip():
            indent = ' ' * len(indent)
        out.append((m.group(1), m.start(), i, t[m.start():i], indent))
    return out


# ==========================================================================
# base - the centring, and the one dismiss script
# ==========================================================================
BASE_CSS_WAS = """      .alv-tag-sky   { color: var(--alv-tag-sky-ink); background: var(--alv-tag-sky-soft); border-color: var(--alv-tag-sky-line); }"""

BASE_CSS_NOW = """      /* ===== ALV MESSAGE v1 ===== 29 Sep 2026
         The bar Django's messages framework renders. 77 loops across the
         tree wrote it sixteen different ways; they now write one, and
         .alv-message is what marks a bar as one of THOSE rather than one
         of the twenty static alerts a page puts in its own content.

         THE TEXT STAYS CENTRED. Fifty-odd of the loops centred it with a
         <center> tag - deprecated, and what the G-series is removing. It
         is a rule here instead, so the only thing that moved on the
         screen when the round landed was the colour.

         The close button is Bootstrap's, positioned absolutely, so the
         centred text needs room on both sides rather than one.
                                                 [test_message_bar.py] */
      .alv-message { text-align: center; }
      .alv-message.alert-dismissible { padding-right: 52px; padding-left: 52px; }
      @media screen and (max-width: 768px) {
        .alv-message.alert-dismissible { padding-right: 44px; padding-left: 16px; text-align: left; }
      }

      .alv-tag-sky   { color: var(--alv-tag-sky-ink); background: var(--alv-tag-sky-soft); border-color: var(--alv-tag-sky-line); }"""

BASE_JS_ANCHOR = """  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.querySelector('.action-filter');"""

BASE_JS = """  /* ===== THE MESSAGE BAR'S OWN TIMER ===== 29 Sep 2026
     Fifty-one pages carried this script, identical, INSIDE the message
     loop - so a page with three messages emitted it three times, and the
     behaviour of every bar in the system was decided in fifty-one
     places.

     WHICH BARS FADE IS THE DECISION, AND IT CHANGED. Every bar used to
     go after two seconds, errors included. With the bars taking their
     colour from the tag there are far more red ones - errors outnumber
     successes 281 to 158 - and a failure that disappears before it can
     be read is worse than the grey one it replaced.

     So: a SUCCESS or an INFORMATION bar leaves on its own, because it
     reports something that went fine and needs no action. A DANGER or a
     WARNING bar waits to be dismissed. Two seconds is the timing the 51
     copies used and it is kept, so only the WHICH changed, not the HOW
     LONG.
                                                 [test_message_bar.py] */
  document.addEventListener('DOMContentLoaded', function () {
    var fading = document.querySelectorAll(
      '.alv-message.alert-success, .alv-message.alert-info');
    if (!fading.length) return;
    setTimeout(function () {
      Array.prototype.forEach.call(fading, function (bar) {
        bar.classList.remove('show');
        bar.classList.add('fade');
        setTimeout(function () { bar.remove(); }, 500);
      });
    }, 2000);
  });

  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.querySelector('.action-filter');"""

# ==========================================================================
# The calendar's notice - information, not a success
# ==========================================================================
CAL_WAS = """.mobile-view-banner {
    display: none;
    background: linear-gradient(135deg, #e7f5f8 0%, #d4edda 100%);
    border: 1px solid #b8daff;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 16px;
    font-size: 13px;
    color: #495057;
    text-align: center;
}
.mobile-view-banner i {
    color: #0e7c8b;
    margin-right: 6px;
}"""

CAL_NOW = """/* IT EXPLAINS WHAT YOU ARE LOOKING AT - it does not report that
   something happened. It was a gradient running from an informational
   teal into #d4edda, which is Bootstrap's SUCCESS green, so it ended in
   the colour this system uses for "that worked". Flat accent now, on the
   tokens, and green goes back to meaning one thing. */
.mobile-view-banner {
    display: none;
    background: var(--alv-accent-soft);
    border: 1px solid var(--alv-accent-line);
    border-radius: var(--alv-radius);
    padding: 10px 14px;
    margin-bottom: 16px;
    font-size: 13px;
    color: var(--alv-ink-strong);
    text-align: center;
}
.mobile-view-banner i {
    color: var(--alv-accent);
    margin-right: 6px;
}"""

# ==========================================================================
print('=' * 74)
print('SECTION M, ROUND M1 - THE MESSAGE BAR SAYS WHAT HAPPENED%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ---- 1. THE PRECONDITION, FIRST ----------------------------------------
p = os.path.join(os.getcwd(), SETTINGS)
t, raw = read(p)
print('  %s' % SETTINGS)
if 'MESSAGE_TAGS' in t:
    print('     MESSAGE_TAGS is already set')
else:
    t = swap(t, p, SET_WAS, SET_NOW, 'MESSAGE_TAGS maps ERROR to danger',
             SETTINGS)
    if not CHECK:
        back_up(p, raw)
        write(p, t)
    # NOTHING ELSE RUNS UNTIL THIS IS TRUE.
    if "MESSAGE_TAGS = {message_constants.ERROR: 'danger'}" not in t:
        raise SystemExit('M1: the precondition did not land, and without it '
                         'every error message renders unstyled')

# ---- 2. ONE SHAPE, 77 TIMES --------------------------------------------
print('  the message loops')
pages = done = 0
for q in alv_tree.templates():
    t, raw = read(q)
    ls = loops(t)
    if not ls:
        continue
    if all('alv-message' in b for _v, _a, _b2, b, _i in ls):
        continue
    out, last = [], 0
    for var, a, b, block, indent in ls:
        out.append(t[last:a])
        out.append(eol(q, BAR % {'v': var, 'i': indent}))
        last = b
        done += 1
    out.append(t[last:])
    t = ''.join(out)

    # THE SCRIPTS THAT WERE INSIDE THE LOOPS ARE NOW OUTSIDE NOTHING.
    t = re.sub(r'\n[ \t]*<script>\s*setTimeout\(function\(\) \{\s*'
               r'document\.querySelectorAll\(\'\.auto-dismiss\'\).*?'
               r'</script>', '', t, flags=re.S)

    if 'auto-dismiss' in t and 'alert' in t:
        # A page may still carry the CLASS on a static alert of its own.
        for m in re.finditer(r'auto-dismiss', t):
            pass
    if not CHECK:
        back_up(q, raw)
        write(q, t)
    pages += 1
print('     %d loop(s) across %d page(s), all one shape' % (done, pages))

# ---- 2b. THE THREE THE LOOP PASS COULD NOT SEE ------------------------
#
#   Two pages kept a COPY of the timer at page level rather than inside
#   the loop, so removing the in-loop copies left them selecting nothing:
#   their bars no longer carry .auto-dismiss, because the bars were
#   rewritten. Dead script, and it is this round's to remove.
#
#   The third is not a Django message at all. generate_lease_agreement
#   BUILDS a success bar in JavaScript, wearing alert-secondary - grey,
#   for a thing that worked - plus auto-dismiss and a <center>. It is a
#   success, so it says so, and base's timer then fades it like any
#   other success.
ORPHANS = [
    ('act_expense.html', """
// Auto-dismiss alerts
setTimeout(function() {
    document.querySelectorAll('.auto-dismiss').forEach(alert => {
        alert.classList.remove('show');
        alert.classList.add('fade');
        setTimeout(() => alert.remove(), 500);
    });
}, 2000);
""", "\n"),
    ('property_management_dashboard.html', """
  // Auto-dismiss messages
  setTimeout(function() {
    document.querySelectorAll('.auto-dismiss').forEach(function(alert) {
      alert.classList.remove('show');
      alert.classList.add('fade');
      setTimeout(function() { alert.remove(); }, 500);
    });
  }, 2000);
""", "\n"),
]

LEASE = 'generate_lease_agreement.html'
LEASE_WAS = """        <div class="alert alert-secondary alert-dismissible fade show auto-dismiss" role="alert" id="lease-success-message">
          <strong></strong> <center>Lease agreement generated successfully!</center>"""
LEASE_NOW = """        <div class="alert alert-success alert-dismissible fade show alv-message" role="alert" id="lease-success-message">
          Lease agreement generated successfully!"""

print('  the three the loop pass could not see')
for name, was, now in ORPHANS:
    q = alv_tree.path_of(name)
    t, raw = read(q)
    if 'auto-dismiss' not in t:
        print('     %-38s already done' % name)
        continue
    t = swap(t, q, was, now,
             '%-34s the orphaned timer, which now selects nothing' % name,
             name)
    if 'auto-dismiss' in t:
        raise SystemExit('M1: %s still mentions auto-dismiss' % name)
    if not CHECK:
        back_up(q, raw)
        write(q, t)

q = alv_tree.path_of(LEASE)
t, raw = read(q)
if 'auto-dismiss' not in t:
    print('     %-38s already done' % LEASE)
else:
    t = swap(t, q, LEASE_WAS, LEASE_NOW,
             '%-34s the JS-built bar says success, and loses its <center>'
             % LEASE, LEASE)
    if not CHECK:
        back_up(q, raw)
        write(q, t)

# ---- 3. base ------------------------------------------------------------
p = alv_tree.path_of(BASE)
t, raw = read(p)
print('  %s' % BASE)
if '.alv-message' in t:
    print('     already carries the component')
else:
    t = swap(t, p, BASE_CSS_WAS, BASE_CSS_NOW,
             'the bar centres itself, without a <center>', BASE)
    t = swap(t, p, BASE_JS_ANCHOR, BASE_JS,
             'and one timer: success and info fade, danger and warning '
             'stay', BASE)
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- 3b. THE ONE TONE THE HOUSE NEVER OWNED ---------------------------
#
#   base overrides .alert-info, .alert-success and .alert-warning with the
#   house tokens, and stops. .alert-danger is Bootstrap's own #f8d7da on
#   #721c24 - and after this round the danger bar is the COMMONEST bar in
#   the system: 281 messages.error(...) against 158 successes. The one
#   tone that says a thing failed would have been the one tone that is
#   not ours.
#
#   --alv-bad also had no -ink or -line sibling, though --alv-good and
#   --alv-warn both do. MEASURED, to sit with them: --alv-good-ink is
#   7.56 on its tint and --alv-warn-ink is 7.34; #8f1d17 on
#   --alv-bad-soft is 7.66. The line is the value .alv-pill-bad already
#   used for its edge.
BAD_TOK_WAS = """        --alv-bad:        #b3261e;
        --alv-bad-soft:   #fbeae9;"""
BAD_TOK_NOW = """        --alv-bad:        #b3261e;
        --alv-bad-soft:   #fbeae9;
        --alv-bad-ink:    #8f1d17;   /* ink on the tint - measures 7.66  */
        --alv-bad-line:   #f2cecb;   /* the tint's own edge              */"""

BAD_RULE_WAS = """      .alert-success {
        background-color: var(--alv-good-soft);
        border-color: var(--alv-good-line);
        color: var(--alv-good-ink);
      }"""
BAD_RULE_NOW = """      .alert-success {
        background-color: var(--alv-good-soft);
        border-color: var(--alv-good-line);
        color: var(--alv-good-ink);
      }
      /* THE ONE THAT WAS MISSING - 29 Sep. info, success and warning were
         all brought onto the tokens; danger was left as Bootstrap's own,
         and M1 makes it the commonest bar on the system. */
      .alert-danger {
        background-color: var(--alv-bad-soft);
        border-color: var(--alv-bad-line);
        color: var(--alv-bad-ink);
      }"""

p = alv_tree.path_of(BASE)
t, raw = read(p)
print('  %s - the danger tone' % BASE)
if '--alv-bad-ink' in t:
    print('     already owns .alert-danger')
else:
    t = swap(t, p, BAD_TOK_WAS, BAD_TOK_NOW,
             '--alv-bad-ink and --alv-bad-line complete the family', BASE)
    t = swap(t, p, BAD_RULE_WAS, BAD_RULE_NOW,
             'and .alert-danger joins info, success and warning', BASE)
    toks = len(set(re.findall(r'(--alv-[a-z0-9-]+)\s*:', t)))
    said = re.search(r'(\d+) design tokens', t)
    if said and int(said.group(1)) != toks:
        t = t.replace('%s design tokens' % said.group(1),
                      '%d design tokens' % toks, 1)
        print('     the standards block: %s design tokens -> %d'
              % (said.group(1), toks))
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- 4. the calendar's notice -------------------------------------------
p = alv_tree.path_of(CAL)
t, raw = read(p)
print('  %s' % CAL)
if 'linear-gradient(135deg, #e7f5f8' not in t:
    print('     the notice is already on the tokens')
else:
    t = swap(t, p, CAL_WAS, CAL_NOW,
             'the timeline notice: accent, not a green gradient', CAL)
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- 5. TWO SUITES MUST KEEP JUDGING THEIR OWN ROUNDS -----------------
#
#   Lesson 17, twice more, and both times this round is the trigger.
#
#   test_event_tones.py (C1) controls that C1 added exactly TEN tokens to
#   base, by diffing base now against C1's own backup. M1 adds two more,
#   so it reads twelve. C1 added ten; the sentence is still true and the
#   measurement had stopped being about C1.
#
#   test_print_buttons.py renders every page's markup as it is TODAY
#   against the page as that round found it, and requires that only
#   buttons left. M1 removes a <strong></strong> and a <center> from 77
#   bars, so the element counts differ and it reports "something else
#   moved". They did move - four rounds later, and not by that round.
#   Its SCREEN comparison was already fixed this way on 21 Sep; its
#   PRINT comparison was left behind.
#
#   Both take the same repair the programme already uses: as_left_by().
EV = 'test_event_tones.py'
EV_WAS = """    old_toks = len(set(re.findall(r'(--alv-[a-z0-9-]+)\\s*:',
                                  css_of(read(b)))))
    ok(toks - old_toks == 10,"""
EV_NOW = """    old_toks = len(set(re.findall(r'(--alv-[a-z0-9-]+)\\s*:',
                                  css_of(read(b)))))
    # AND base AS THIS ROUND LEFT IT, not as it is now. M1 added two more
    # tokens on 29 Sep and this control read twelve - C1 still added ten.
    try:
        from alv_rounds import as_left_by
        mine_toks = len(set(re.findall(
            r'(--alv-[a-z0-9-]+)\\s*:',
            css_of(as_left_by(alv_tree.path_of('base.html'), SUFFIX,
                              read)))))
    except Exception:
        mine_toks = toks
    ok(mine_toks - old_toks == 10,"""
EV_TAIL_WAS = """       'lines', '%d -> %d' % (old_toks, toks))"""
EV_TAIL_NOW = """       'lines', '%d -> %d' % (old_toks, mine_toks))"""

q = os.path.join(os.getcwd(), EV)
t, raw = read(q)
print('  %s' % EV)
if 'mine_toks' in t:
    print('     already counts base as C1 left it')
else:
    t = swap(t, q, EV_WAS, EV_NOW, 'its token control reads base as C1 '
             'left it', EV)
    t = swap(t, q, EV_TAIL_WAS, EV_TAIL_NOW, '  and reports that number',
             EV)
    if not CHECK:
        back_up(q, raw)
        write(q, t)

PB = 'test_print_buttons.py'
PB_WAS = """        for rel, p in all_pages:
            t = read(p)
            mk = body_markup(t)"""
PB_NOW = """        from alv_rounds import as_left_by
        for rel, p in all_pages:
            t = read(p)
            mk = body_markup(t)
            # THE PAGE AS THIS ROUND LEFT IT, for the before/after below.
            # `t` stays TODAY'S markup, because the .print-keep promise
            # above is about every page as it stands - but comparing
            # today's element COUNT against the day of the round makes
            # every later round's edit look like this one's. M1 took a
            # <strong></strong> and a <center> out of 77 message bars on
            # 29 Sep and this reported 411 elements moving. The screen
            # comparison below was given as_left_by on 21 Sep; the print
            # comparison was left behind.
            lt = as_left_by(p, SUFFIX, read)
            lmk = body_markup(lt)"""
PB_NOW_RENDER_WAS = """            old_t = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else t
            old_mk = body_markup(old_t)
            was = render(br, fixture(boot, base_was, styles_of(old_t),
                                     old_mk), 718, 'print', SEEN, BTN)
            if len(was) != len(now):"""
PB_NOW_RENDER_NOW = """            old_t = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else lt
            old_mk = body_markup(old_t)
            was = render(br, fixture(boot, base_was, styles_of(old_t),
                                     old_mk), 718, 'print', SEEN, BTN)
            mine = render(br, fixture(boot, '\\n'.join(styles_of(
                as_left_by(BASE_PATH, SUFFIX, read))), styles_of(lt), lmk),
                718, 'print', SEEN, BTN)
            now = mine
            if len(was) != len(now):"""

q = os.path.join(os.getcwd(), PB)
t, raw = read(q)
print('  %s' % PB)
if 'lmk = body_markup(lt)' in t:
    print('     already compares the page as its own round left it')
else:
    t = swap(t, q, PB_WAS, PB_NOW,
             'its print comparison reads the page as its round left it', PB)
    t = swap(t, q, PB_NOW_RENDER_WAS, PB_NOW_RENDER_NOW,
             '  and renders that side rather than today\'s', PB)
    if not CHECK:
        back_up(q, raw)
        write(q, t)

# ---- 5b. AND A THIRD, FOR THE SAME REASON ------------------------------
#
#   test_table_admin.py requires its two pages to still read every Django
#   expression they read before its round - a good check, and it compares
#   today's file against its own backup. M1 takes the hand-rolled
#   {% if 'success' in msg.tags %} branches out of both message bars,
#   which is the whole point of the round, so it reports them lost.
#
#   Third time today, same repair.
TA = 'test_table_admin.py'
TA_WAS = """        a, b = expressions(read(bak)), expressions(read(p))"""
TA_NOW = """        # THE FILE AS THIS ROUND LEFT IT. M1 collapsed 77 message bars
        # onto one shape on 29 Sep, taking the hand-rolled
        # {% if 'success' in msg.tags %} branches out of these two - a
        # later round's edit, not an expression this one dropped.
        try:
            from alv_rounds import as_left_by
            mine = as_left_by(p, SUFFIX, read)
        except Exception:
            mine = read(p)
        a, b = expressions(read(bak)), expressions(mine)"""

q = os.path.join(os.getcwd(), TA)
t, raw = read(q)
print('  %s' % TA)
if 'as_left_by' in t:
    print('     already reads the page as its own round left it')
else:
    t = swap(t, q, TA_WAS, TA_NOW,
             'its expression census reads the page as its round left it',
             TA)
    if not CHECK:
        back_up(q, raw)
        write(q, t)

# ---- THE GATES ----------------------------------------------------------
shapes, scripts, centres, errs = set(), 0, 0, []
for q in alv_tree.templates():
    t2 = read(q)[0]
    for var, a, b, block, indent in loops(t2):
        # NORMALISE THE TEMPLATE VARIABLE, NOT EVERY WORD. The first
        # version replaced \bmessage\b and turned the class name
        # alv-message into alv-VAR on the five loops whose variable is
        # `message` - so the gate reported two shapes where there is
        # one. Replace the three places a loop variable can appear.
        flat = ' '.join(block.split())
        for was_, now_ in (('for %s in' % var, 'for VAR in'),
                           ('{{ %s ' % var, '{{ VAR '),
                           ('{{ %s.' % var, '{{ VAR.')):
            flat = flat.replace(was_, now_)
        shapes.add(flat)
        if '<center>' in block:
            centres += 1
        if '<script>' in block:
            scripts += 1
        if 'alert-error' in block:
            errs.append(alv_tree.rel(q))

print('-' * 74)
if not CHECK:
    if len(shapes) != 1:
        raise SystemExit('M1: the loops are in %d shapes, not 1:\n%s'
                         % (len(shapes), '\n'.join(sorted(shapes))[:600]))
    if scripts:
        raise SystemExit('M1: %d loop(s) still carry a script' % scripts)
    if centres:
        raise SystemExit('M1: %d loop(s) still use <center>' % centres)
    if errs:
        raise SystemExit('M1: alert-error would render on %s' % errs)
    print('  every message loop in the tree is the SAME shape, and it is')
    print('  the only shape.')
else:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
