# -*- coding: utf-8 -*-
"""apply_ra02_travel_more.py - round RA02, 19 Nov 2026.

RELEASE RA02 - TRAVEL: THE ACTION BAR ON A PHONE, AS THE HOUSE DOES IT.

    Demetri, 19 Nov: "The buttons on top of the travel section of the
    desktop version viewed on a mobile are not as per our standards (not
    in the downloaded app, but the desktop version)".

    The house standard (base 3.4): below 768px the primary takes the row,
    the secondaries move into the More menu, Back is a 44px square. The
    trip page (Add booking + six) and the trips list (New trip + five) had
    no More menu, so on a phone the buttons were squeezed to slivers.
    Both now carry one, listing every secondary (the PDF chooser as PDF -
    summary and PDF - detailed). Every other Travel bar already fits.
    Help says where the buttons went.

The suite ships beside this patcher. Stands on RA01. Idempotent. Edits
backed up to .bak_ra02. No migration.
"""
import os
import sys

SUFFIX = '.bak_ra02'
MARK = 'RA02, 19 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra02_travel_more.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_travel_sixteen.py',
    # RA01, 18 Nov 2026 - Compare in the trip card, proper drop-downs.
    'test_ra01_trip_cards.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_travel_sixteen.py',
    # RA01, 18 Nov 2026 - Compare in the trip card, proper drop-downs.
    'test_ra01_trip_cards.py',
    # RA02, 19 Nov 2026 - the Travel action bar on a phone.
    'test_ra02_travel_more.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA01, 18 Nov 2026 - Compare in the trip card, proper drop-downs.
    '.bak_ra01',
]

''',
         r'''    # RA01, 18 Nov 2026 - Compare in the trip card, proper drop-downs.
    '.bak_ra01',
    # RA02, 19 Nov 2026 - the Travel action bar on a phone.
    '.bak_ra02',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p>Every Travel page has a <strong>Help</strong> button that opens these pages; on the phone, tap the <strong>?</strong> at the top right.</p>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first; with nothing coming up it shows your <strong>Past</strong> trips instead, each marked <em>Past</em>. Every list has the latest trip at the top and the oldest at the bottom. Across the top are <strong>All</strong>, <strong>Upcoming</strong> and <strong>Past</strong>, each with its number of trips in a small grey badge, then two menus: <strong>Year</strong> (newest first) and <strong>Country</strong> (the countries you go to most at the top) &mdash; press either and its list opens, each choice with its number of trips. Pick a year or a country and it becomes a highlighted chip &mdash; press its &#x2715; to clear it. They combine: Past, 2026 and Greece shows the past trips of 2026 in Greece, and the numbers in the badges follow what you picked. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Calendar.</strong> <strong>List | Calendar</strong> at the top of Travel switches to a month calendar with every trip on it as a coloured bar across its days &ndash; paler once it is over &ndash; and a <i class="fas fa-plane"></i> on each day you fly. It opens on this month with today circled; <strong>&lsaquo; &rsaquo;</strong> move a month at a time, the month and year boxes jump straight to any month, and <strong>Today</strong> brings you back. Click a trip&rsquo;s bar to open its itinerary. Travel remembers which view you used last. On the phone, Trips has the same switch; swipe left or right for the next or last month, and the month&rsquo;s trips are listed under it.</p>
    <p><strong>Compare trips.</strong> Tick <em>Compare</em> at the foot of two or more trip cards &mdash; a ticked card is outlined, and the button counts them &mdash; and press <strong>Compare ticked trips</strong>. You see each trip&rsquo;s total, cost a day and cost a person, then like for like: the hotel per night, flights per person per flight (a return counts as two flights), car hire per day, trains per journey, restaurants per meal, activities and the whole trip per day &mdash; the cheapest marked, anything 20% or more above the average marked too &mdash; where the money went, a few lines on what stands out, and every hotel ranked by its price a night. Everything is in euros, worked out from the bookings, cancelled ones left out. Add or take out a trip at the top. On the phone, <strong>Trips &rarr; Compare</strong> shows the main figures.</p>
''',
         r'''    <p>Every Travel page has a <strong>Help</strong> button that opens these pages; on the phone, tap the <strong>?</strong> at the top right.</p>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities, restaurants &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first; with nothing coming up it shows your <strong>Past</strong> trips instead, each marked <em>Past</em>. Every list has the latest trip at the top and the oldest at the bottom. On a phone&rsquo;s browser the buttons above follow the house pattern: <strong>New trip</strong> (or <strong>Add booking</strong> inside a trip) fills the row, everything else is under the <strong>&#8942;</strong> button beside it, and Back is the small square on the right. Across the top are <strong>All</strong>, <strong>Upcoming</strong> and <strong>Past</strong>, each with its number of trips in a small grey badge, then two menus: <strong>Year</strong> (newest first) and <strong>Country</strong> (the countries you go to most at the top) &mdash; press either and its list opens, each choice with its number of trips. Pick a year or a country and it becomes a highlighted chip &mdash; press its &#x2715; to clear it. They combine: Past, 2026 and Greece shows the past trips of 2026 in Greece, and the numbers in the badges follow what you picked. Each card shows the total, what is paid and what is still to pay.</p>
    <p><strong>Calendar.</strong> <strong>List | Calendar</strong> at the top of Travel switches to a month calendar with every trip on it as a coloured bar across its days &ndash; paler once it is over &ndash; and a <i class="fas fa-plane"></i> on each day you fly. It opens on this month with today circled; <strong>&lsaquo; &rsaquo;</strong> move a month at a time, the month and year boxes jump straight to any month, and <strong>Today</strong> brings you back. Click a trip&rsquo;s bar to open its itinerary. Travel remembers which view you used last. On the phone, Trips has the same switch; swipe left or right for the next or last month, and the month&rsquo;s trips are listed under it.</p>
    <p><strong>Compare trips.</strong> Tick <em>Compare</em> at the foot of two or more trip cards &mdash; a ticked card is outlined, and the button counts them &mdash; and press <strong>Compare ticked trips</strong>. You see each trip&rsquo;s total, cost a day and cost a person, then like for like: the hotel per night, flights per person per flight (a return counts as two flights), car hire per day, trains per journey, restaurants per meal, activities and the whole trip per day &mdash; the cheapest marked, anything 20% or more above the average marked too &mdash; where the money went, a few lines on what stands out, and every hotel ranked by its price a night. Everything is in euros, worked out from the bookings, cancelled ones left out. Add or take out a trip at the top. On the phone, <strong>Trips &rarr; Compare</strong> shows the main figures.</p>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-picked { border: 1.5px solid var(--alv-accent); background: rgba(14, 124, 139, .08); color: var(--alv-accent); font-weight: 700; }
.tv-picked .tv-x { font-size: 0.8rem; }
.tv-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.tv-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
''',
         r'''.tv-picked { border: 1.5px solid var(--alv-accent); background: rgba(14, 124, 139, .08); color: var(--alv-accent); font-weight: 700; }
.tv-picked .tv-x { font-size: 0.8rem; }
/* RA02, 19 Nov 2026 - on a phone the PDF chooser lives in the More menu; its desktop wrapper steps aside with its button. */
@media screen and (max-width: 768px) { .page-action-buttons:has(.action-more-btn) > .tv-menu { display: none; } }
.tv-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.tv-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''    {% if is_owner %}<a href="{% url 'travel:trip_merge' trip.pk %}" class="btn action-secondary"><i class="fas fa-object-group"></i> Merge</a>{% endif %}
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
''',
         r'''    {% if is_owner %}<a href="{% url 'travel:trip_merge' trip.pk %}" class="btn action-secondary"><i class="fas fa-object-group"></i> Merge</a>{% endif %}
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    {% comment %} RA02, 19 Nov 2026 (Demetri: "The buttons on top of the travel section of the desktop version viewed on a mobile are not as per our standards"). The house standard (base 3.4): below 768px Add booking takes the row, the rest move into the More menu, Back is a square. {% endcomment %}
    <div class="action-more-wrapper" data-menu data-travel-more>
        <button type="button" class="btn action-more-btn" data-menu-toggle aria-label="More actions" aria-expanded="false" aria-haspopup="true"><i class="fas fa-ellipsis-v"></i></button>
        <div class="action-more-menu" data-menu-panel role="menu" hidden>
            <a class="action-more-item" role="menuitem" href="{% url 'travel:place_new' trip.pk %}"><i class="fas fa-plus"></i> Things to do</a>
            {% if is_owner %}<a class="action-more-item" role="menuitem" href="{% url 'travel:trip_share' trip.pk %}"><i class="fas fa-share-alt"></i> Share</a>{% endif %}
            <a class="action-more-item" role="menuitem" href="{% url 'travel:trip_edit' trip.pk %}"><i class="fas fa-pen"></i> Edit trip</a>
            <button type="button" class="action-more-item" role="menuitem" onclick="openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=summary', '{{ trip.name|escapejs }} - summary', 'trip_{{ trip.name|slugify }}_summary.pdf')"><i class="fas fa-file-pdf"></i> PDF - summary</button>
            <button type="button" class="action-more-item" role="menuitem" onclick="openPdfViewer('{% url 'travel:trip_pdf' trip.pk %}?kind=detailed', '{{ trip.name|escapejs }} - detailed', 'trip_{{ trip.name|slugify }}_detailed.pdf')"><i class="fas fa-file-pdf"></i> PDF - detailed</button>
            {% if is_owner %}<a class="action-more-item" role="menuitem" href="{% url 'travel:trip_merge' trip.pk %}"><i class="fas fa-object-group"></i> Merge</a>{% endif %}
            <button type="button" class="action-more-item" role="menuitem" data-toggle="modal" data-target="#travelHelpModal"><i class="fas fa-question-circle"></i> Help</button>
        </div>
    </div>
    <a href="{% url 'travel:trips' %}" class="btn action-back" aria-label="Back to Travel">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trips.html'), [
        (r'''    <a href="?show={{ show }}&amp;phone=1" class="btn action-secondary" data-phone-button><i class="fas fa-mobile-alt"></i> Phone app</a>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    <a href="{% url 'personal_page' %}" class="btn action-back" aria-label="Back to Personal">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
''',
         r'''    <a href="?show={{ show }}&amp;phone=1" class="btn action-secondary" data-phone-button><i class="fas fa-mobile-alt"></i> Phone app</a>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#travelHelpModal" title="How Travel works" data-travel-help><i class="fas fa-question-circle"></i> Help</button>
    {% comment %} RA02, 19 Nov 2026 - the house standard on a phone: New trip takes the row, the rest in the More menu, Back a square. {% endcomment %}
    <div class="action-more-wrapper" data-menu data-travel-more>
        <button type="button" class="btn action-more-btn" data-menu-toggle aria-label="More actions" aria-expanded="false" aria-haspopup="true"><i class="fas fa-ellipsis-v"></i></button>
        <div class="action-more-menu" data-menu-panel role="menu" hidden>
            <a class="action-more-item" role="menuitem" href="{% url 'travel:check' %}"><i class="fas fa-inbox"></i> To check{% if checks %} <span class="tv-count">{{ checks }}</span>{% endif %}</a>
            <a class="action-more-item" role="menuitem" href="{% url 'travel:forwarding' %}"><i class="fas fa-envelope"></i> Forwarding</a>
            <a class="action-more-item" role="menuitem" href="{% url 'travel:passes' %}"><i class="fas fa-qrcode"></i> Boarding passes</a>
            <a class="action-more-item" role="menuitem" href="?show={{ show }}&amp;phone=1"><i class="fas fa-mobile-alt"></i> Phone app</a>
            <button type="button" class="action-more-item" role="menuitem" data-toggle="modal" data-target="#travelHelpModal"><i class="fas fa-question-circle"></i> Help</button>
        </div>
    </div>
    <a href="{% url 'personal_page' %}" class="btn action-back" aria-label="Back to Personal">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
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
    raise SystemExit('RA02 REFUSED: %s' % msg)


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
    if "'test_ra02_travel_more.py'" in read(pq):
        print('RA02 already applied.')
        return 0
    if "'test_ra01_trip_cards.py'" not in read(pq):
        refuse('RA01 (apply_ra01_trip_cards.py) is not applied - this round registers after it.')
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
        print('RA02 --check: %d file(s) would change, none written; %d '
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
    print('RA02 applied - the Travel action bar on a phone.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
