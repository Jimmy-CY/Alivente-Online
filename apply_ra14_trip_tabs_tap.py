# -*- coding: utf-8 -*-
"""apply_ra14_trip_tabs_tap.py - round RA14, 22 Nov 2026.

RELEASE RA14 - THE PHONE'S TRIP TABS OPEN AGAIN.

    Demetri, 22 Nov: "Buttons look good on mobile. But don't work when
    you press them".

    - RA13 marked the phone's trip tabs data-tab="..."; travel.js takes
      every [data-tab] for its own in-page tabs (the boarding passes),
      cancelled the tap and looked for a panel the trip page has not got.
      They are marked data-trip-tab now - plain links again.
    - test_ra13_trip_tabs checks the new mark.
    - No migration; no Help change (nothing works differently).

The suite ships beside this patcher. Stands on RA13. Idempotent. Edits
backed up to .bak_ra14.
"""
import os
import sys

SUFFIX = '.bak_ra14'
MARK = 'RA14, 22 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra14_trip_tabs_tap.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra12_city_info_receipts.py',
    # RA13, 22 Nov 2026 - the trip tabs: icons, short names on the phone.
    'test_ra13_trip_tabs.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra12_city_info_receipts.py',
    # RA13, 22 Nov 2026 - the trip tabs: icons, short names on the phone.
    'test_ra13_trip_tabs.py',
    # RA14, 22 Nov 2026 - the phone's trip tabs open again.
    'test_ra14_trip_tabs_tap.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA13, 22 Nov 2026 - the trip tabs: icons, short names on the phone.
    '.bak_ra13',
]

''',
         r'''    # RA13, 22 Nov 2026 - the trip tabs: icons, short names on the phone.
    '.bak_ra13',
    # RA14, 22 Nov 2026 - the phone's trip tabs open again.
    '.bak_ra14',
]

'''),
    ]),
    (os.path.join('test_ra13_trip_tabs.py'), [
        (r'''               '<span>Plan</span>' in nav and '<span>Info</span>' in nav,
               'THE PHONE PAGE: an icon on every tab, short names')
            ok('data-tab="wish" aria-label="Things to do" aria-current="page"'
               in nav, '  the open tab is marked')
            A = Client(SERVER_NAME='localhost')
            A.force_login(me)
''',
         r'''               '<span>Plan</span>' in nav and '<span>Info</span>' in nav,
               'THE PHONE PAGE: an icon on every tab, short names')
            ok('data-trip-tab="wish" aria-label="Things to do" '
               'aria-current="page"' in nav, '  the open tab is marked')
            A = Client(SERVER_NAME='localhost')
            A.force_login(me)
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>{% endblock %}
{% block tabs %}{% comment %} RA13, 22 Nov 2026 - icon tabs, all on one line, short names (the computer keeps the full ones). {% endcomment %}<nav class="tv-tabs is-icons" aria-label="Trip"><a class="tv-tab{% if sub == 'bookings' %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}" data-tab="bookings"{% if sub == 'bookings' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='bookings' %}<span>Bookings</span></a><a class="tv-tab{% if sub == 'itinerary' %} on{% endif %}" href="?tab=itinerary" data-tab="itinerary" aria-label="Itinerary"{% if sub == 'itinerary' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='itinerary' %}<span>Plan</span></a><a class="tv-tab{% if sub == 'wish' %} on{% endif %}" href="?tab=wish" data-tab="wish" aria-label="Things to do"{% if sub == 'wish' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='wish' %}<span>To do</span></a>{% if show_money %}<a class="tv-tab{% if sub == 'costs' %} on{% endif %}" href="?tab=costs" data-tab="costs"{% if sub == 'costs' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='costs' %}<span>Costs</span></a>{% endif %}<a class="tv-tab{% if sub == 'info' %} on{% endif %}" href="?tab=info" data-tab="info" data-tab-info aria-label="Good to know"{% if sub == 'info' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='info' %}<span>Info</span></a></nav>{% endblock %}
{% block content %}
{% if sub == 'itinerary' %}
''',
         r'''{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trips' %}"><span aria-hidden="true">‹</span> Trips</a><h1>{{ trip.name }}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if trip.start %}{{ trip.start|date:"D j M" }}{% if trip.end and trip.end != trip.start %} – {{ trip.end|date:"D j M Y" }}{% endif %}{% endif %}{% if trip.where %} · {{ trip.where }}{% endif %}</div>{% endblock %}
{% block tabs %}{% comment %} RA13, 22 Nov 2026 - icon tabs, all on one line, short names (the computer keeps the full ones). RA14 - marked data-trip-tab, not data-tab: travel.js takes every [data-tab] for its own in-page tabs and stopped these links. {% endcomment %}<nav class="tv-tabs is-icons" aria-label="Trip"><a class="tv-tab{% if sub == 'bookings' %} on{% endif %}" href="{% url 'travel:m_trip' trip.pk %}" data-trip-tab="bookings"{% if sub == 'bookings' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='bookings' %}<span>Bookings</span></a><a class="tv-tab{% if sub == 'itinerary' %} on{% endif %}" href="?tab=itinerary" data-trip-tab="itinerary" aria-label="Itinerary"{% if sub == 'itinerary' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='itinerary' %}<span>Plan</span></a><a class="tv-tab{% if sub == 'wish' %} on{% endif %}" href="?tab=wish" data-trip-tab="wish" aria-label="Things to do"{% if sub == 'wish' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='wish' %}<span>To do</span></a>{% if show_money %}<a class="tv-tab{% if sub == 'costs' %} on{% endif %}" href="?tab=costs" data-trip-tab="costs"{% if sub == 'costs' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='costs' %}<span>Costs</span></a>{% endif %}<a class="tv-tab{% if sub == 'info' %} on{% endif %}" href="?tab=info" data-trip-tab="info" data-tab-info aria-label="Good to know"{% if sub == 'info' %} aria-current="page"{% endif %}>{% include 'travel/_tab_icon.html' with k='info' %}<span>Info</span></a></nav>{% endblock %}
{% block content %}
{% if sub == 'itinerary' %}
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
    raise SystemExit('RA14 REFUSED: %s' % msg)


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
    if "'test_ra14_trip_tabs_tap.py'" in read(pq):
        print('RA14 already applied.')
        return 0
    if "'test_ra13_trip_tabs.py'" not in read(pq):
        refuse('RA13 (apply_ra13_trip_tabs.py) is not applied - this round registers after it.')
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
        print('RA14 --check: %d file(s) would change, none written; %d '
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
    print('RA14 applied - the phone trip tabs open again. No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
