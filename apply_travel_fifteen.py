# -*- coding: utf-8 -*-
"""apply_travel_fifteen.py - round TR-15, 17 Nov 2026.

RELEASE 96 - TRAVEL: THE PHONE APP FETCHES THE NEW LOOK.

    Demetri, 17 Nov, after R95: "It looks perfect on the Desktop.
    However, it is wrong on the mobile app" - the calendar came out with
    no style. R95 changed travel.css but not the phone's version
    (tv12-1), so the app's worker kept serving its old copy.

    - travel/phone.py: SW_VERSION tv15-1, and SW_ASSETS - the fingerprint
      of travel.css and travel.js it was moved for.
    - m/base.html asks for ?v=tv15-1.
    - test_travel_fifteen.py fails the gate whenever travel.css or
      travel.js change and the version is not moved with them.
    - test_travel_twelve.py: tv12-1 or later.
    - Help says the app fetches a new look by itself.

The suite ships beside this patcher. Stands on TR-14
(apply_travel_fourteen.py). Idempotent. Edits backed up to .bak_travel15.
No migration.
"""
import os
import sys

SUFFIX = '.bak_travel15'
MARK = 'TR-15, 17 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_travel_fifteen.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    # TR-14, 17 Nov 2026 - Release 95: Show me more keeps the ticks and
    # marks the new ones.
    'test_travel_fourteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    # TR-14, 17 Nov 2026 - Release 95: Show me more keeps the ticks and
    # marks the new ones.
    'test_travel_fourteen.py',
    # TR-15, 17 Nov 2026 - Release 96: the phone app fetches the new look.
    'test_travel_fifteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-14, 17 Nov 2026 - Release 95: Show me more keeps the ticks.
    '.bak_travel14',
]

''',
         r'''    # TR-14, 17 Nov 2026 - Release 95: Show me more keeps the ticks.
    '.bak_travel14',
    # TR-15, 17 Nov 2026 - Release 96: the phone's version moves with its style.
    '.bak_travel15',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''           data-tab-icon="fa-mobile-alt">
    <h6><i class="fas fa-mobile-alt"></i> Travel on your phone</h6>
    <p>On the computer, press <strong>Phone app</strong> on the Travel page: a code and six steps. Scan the code with the phone&rsquo;s camera and tap the link (or type <strong>alivente.online/travel/m/</strong> into Chrome), sign in, tap the <strong>three dots &#8942;</strong> at the top right, scroll down to <strong>Add to Home screen</strong> (or <strong>Install app</strong>), choose <strong>Install</strong> &mdash; not <em>Create shortcut</em> &mdash; and <strong>Install</strong> again. On an iPhone: Safari&rsquo;s Share button &rarr; <strong>Add to Home Screen</strong>. It opens like an app and stays signed in for 30 days on the phone, as Wellness does; the rest of Alivente keeps its one-hour sign-in.</p>
    <p><strong>Today</strong> shows today&rsquo;s and tomorrow&rsquo;s bookings while you are away &mdash; flights, check-ins, check-outs, the car &mdash; and before a trip, the days to go and the first day. <strong>Trips</strong> and each booking have everything needed on the day, with Call, Map and Manage buttons and the tickets.</p>
    <p><strong>Passes</strong> has three tabs at the top. <strong>Next</strong> is the flight you need now, full screen, with your own pass first &mdash; swipe sideways for the others on the same flight. <strong>Coming up</strong> lists the flights after it; tap one to open its pass. <strong>Used</strong> keeps every pass for good, stamped <strong>USED</strong> in red with the barcode greyed; <strong>Show the barcode anyway</strong> brings it back in full, as nothing is ever switched off. A pass moves to Used six hours after the flight was due to land (eight hours after it left, if the booking has no landing time), so a delay does not take it away. On a connection &mdash; another flight of yours within a day &mdash; the next pass takes over as soon as the first flight was due to land; before then it is one tap away as <strong>Then: &hellip;</strong> under the pass, and afterwards the first is one tap away as <strong>Earlier today</strong>. Put it right by hand any time: <strong>Done with this pass</strong> moves on at once, and <strong>Not flown yet</strong> on a used pass brings it back to Next for a day. <strong>Add to Google Wallet</strong> goes to the airline until the flight is over; after that a short note explains that airlines stop offering passes to Google Wallet once the flight has flown. The barcode is drawn again from the airline&rsquo;s own code for the scanner to read off the screen &mdash; turn the brightness up; the screen stays on, and turning the phone does not flip the pass: the installed app stays upright, and in a browser the pass is turned back to where it was. Pages you have opened, the passes above all, are kept on the phone and work with no signal; signing out removes them.</p>
''',
         r'''           data-tab-icon="fa-mobile-alt">
    <h6><i class="fas fa-mobile-alt"></i> Travel on your phone</h6>
    <p>On the computer, press <strong>Phone app</strong> on the Travel page: a code and six steps. Scan the code with the phone&rsquo;s camera and tap the link (or type <strong>alivente.online/travel/m/</strong> into Chrome), sign in, tap the <strong>three dots &#8942;</strong> at the top right, scroll down to <strong>Add to Home screen</strong> (or <strong>Install app</strong>), choose <strong>Install</strong> &mdash; not <em>Create shortcut</em> &mdash; and <strong>Install</strong> again. On an iPhone: Safari&rsquo;s Share button &rarr; <strong>Add to Home Screen</strong>. It opens like an app and stays signed in for 30 days on the phone, as Wellness does; the rest of Alivente keeps its one-hour sign-in. After Travel is updated, the app fetches its new look by itself the next time it opens with a signal.</p>
    <p><strong>Today</strong> shows today&rsquo;s and tomorrow&rsquo;s bookings while you are away &mdash; flights, check-ins, check-outs, the car &mdash; and before a trip, the days to go and the first day. <strong>Trips</strong> and each booking have everything needed on the day, with Call, Map and Manage buttons and the tickets.</p>
    <p><strong>Passes</strong> has three tabs at the top. <strong>Next</strong> is the flight you need now, full screen, with your own pass first &mdash; swipe sideways for the others on the same flight. <strong>Coming up</strong> lists the flights after it; tap one to open its pass. <strong>Used</strong> keeps every pass for good, stamped <strong>USED</strong> in red with the barcode greyed; <strong>Show the barcode anyway</strong> brings it back in full, as nothing is ever switched off. A pass moves to Used six hours after the flight was due to land (eight hours after it left, if the booking has no landing time), so a delay does not take it away. On a connection &mdash; another flight of yours within a day &mdash; the next pass takes over as soon as the first flight was due to land; before then it is one tap away as <strong>Then: &hellip;</strong> under the pass, and afterwards the first is one tap away as <strong>Earlier today</strong>. Put it right by hand any time: <strong>Done with this pass</strong> moves on at once, and <strong>Not flown yet</strong> on a used pass brings it back to Next for a day. <strong>Add to Google Wallet</strong> goes to the airline until the flight is over; after that a short note explains that airlines stop offering passes to Google Wallet once the flight has flown. The barcode is drawn again from the airline&rsquo;s own code for the scanner to read off the screen &mdash; turn the brightness up; the screen stays on, and turning the phone does not flip the pass: the installed app stays upright, and in a browser the pass is turned back to where it was. Pages you have opened, the passes above all, are kept on the phone and work with no signal; signing out removes them.</p>
'''),
    ]),
    (os.path.join('test_travel_twelve.py'), [
        (r'''   'HELP: on the computer and the phone')
ph = read(J(TA, 'phone.py'))
ok("SW_VERSION = 'tv12-1'" in ph and '?v=tv12-1' in read(
    J(TT, 'm', 'base.html')),
   'the phone fetches the new style (tv12-1)')

# ==========================================================================
''',
         r'''   'HELP: on the computer and the phone')
ph = read(J(TA, 'phone.py'))
# TR-15 (17 Nov) moved it on: tv12-1 or later, worker and page agreeing.
_v = re.search(r"SW_VERSION = 'tv(\d+)-(\d+)'", ph)
ok(_v and int(_v.group(1)) >= 12 and '?v=tv%s-%s' % _v.groups() in read(
    J(TT, 'm', 'base.html')),
   'the phone fetches the new style (tv12-1 or later)')

# ==========================================================================
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
SW_VERSION = 'tv12-1'


''',
         r'''# or script changes: an installed app keeps the old files until it moves.
# test_travel_three.py checks the two agree.
# TR-15, 17 Nov 2026 (R95 changed travel.css but not this, and the phone
# app kept its old copy - the calendar came out unstyled): the version
# moves whenever travel.css or travel.js does. SW_ASSETS is the fingerprint
# of the two it was moved for; test_travel_fifteen.py fails the gate when
# they change and it does not.
SW_VERSION = 'tv15-1'
SW_ASSETS = 'aace7b3e2c05'


'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv12-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv15-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv12-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv15-1"></script>
</body>
</html>
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('TR-15 REFUSED: %s' % msg)


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

    pq = os.path.join(root, PS1)
    if "'test_travel_fifteen.py'" in read(pq):
        print('TR-15 already applied.')
        return 0
    if "'test_travel_fourteen.py'" not in read(pq):
        refuse('TR-14 (apply_travel_fourteen.py, Release 95) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('TR-15 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('TR-15 applied - the phone app fetches the new look.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
