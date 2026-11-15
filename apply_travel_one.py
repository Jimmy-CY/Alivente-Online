# -*- coding: utf-8 -*-
"""apply_travel_one.py - round TR-1, 15 Nov 2026.

RELEASE 82 - TRAVEL, STAGE 1: trips (your own, or shared like a meal plan),
bookings with every detail and their tickets attached, and the costs in
the original currency and in euros at the ECB rate.

    - A new app, travel/, mounted at /travel/. It ships as files beside
      this patcher, not written by it.
    - A fifth tile on Personal behind a new permission, can_access_travel
      (no edit tier), made by the next migrate.
    - INSTALLED_APPS, the root urls, the middleware, Home, Personal, both
      navigation menus and Help learn about it.

Stands on Release 81. Idempotent. Edits backed up to .bak_travel1.
MIGRATION: travel 0001 - run `python manage.py migrate` after applying.
"""
import os
import sys

SUFFIX = '.bak_travel1'
MARK = 'TR-1, 15 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'travel/__init__.py',
    'travel/apps.py',
    'travel/fx.py',
    'travel/migrations/0001_initial.py',
    'travel/migrations/__init__.py',
    'travel/models.py',
    'travel/templates/travel/_booking_row.html',
    'travel/templates/travel/_style.html',
    'travel/templates/travel/booking.html',
    'travel/templates/travel/booking_form.html',
    'travel/templates/travel/share.html',
    'travel/templates/travel/trip.html',
    'travel/templates/travel/trip_form.html',
    'travel/templates/travel/trips.html',
    'travel/urls.py',
    'travel/views.py',
    'test_travel_one.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_gift_people.py',
    # CG-5, 15 Nov 2026 - Release 81: the gifts pages tidied.
    'test_gift_tidy.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_gift_people.py',
    # CG-5, 15 Nov 2026 - Release 81: the gifts pages tidied.
    'test_gift_tidy.py',
    # TR-1, 15 Nov 2026 - Release 82: Travel, stage 1.
    'test_travel_one.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # CG-5, 15 Nov 2026 - Release 81: the gifts pages tidied.
    '.bak_gifttidy',
]

''',
         r'''    # CG-5, 15 Nov 2026 - Release 81: the gifts pages tidied.
    '.bak_gifttidy',
    # TR-1, 15 Nov 2026 - Release 82: Travel, stage 1.
    '.bak_travel1',
]

'''),
    ]),
    (os.path.join('mysite', 'settings.py'), [
        (r'''    # WL-1, 30 Oct 2026 - Wellness: its own app, outside the house standard.
    "wellness",
    # PK-1, 30 Oct 2026 - sign in with a fingerprint. No templates.
    "passkeys",
''',
         r'''    # WL-1, 30 Oct 2026 - Wellness: its own app, outside the house standard.
    "wellness",
    # TR-1, 15 Nov 2026 - Travel: its own app, like Wellness.
    "travel",
    # PK-1, 30 Oct 2026 - sign in with a fingerprint. No templates.
    "passkeys",
'''),
    ]),
    (os.path.join('mysite', 'urls.py'), [
        (r'''    # shell) answers without a login; everything else needs one.
    path("wellness/", include("wellness.urls")),
    # PK-1, 30 Oct 2026 - passkeys. Under login/ (public, like the
    # password form) and my-profile/ (login only), so the middleware's
''',
         r'''    # shell) answers without a login; everything else needs one.
    path("wellness/", include("wellness.urls")),
    # TR-1, 15 Nov 2026 - Travel, under Personal.
    path("travel/", include("travel.urls")),
    # PK-1, 30 Oct 2026 - passkeys. Under login/ (public, like the
    # password form) and my-profile/ (login only), so the middleware's
'''),
    ]),
    (os.path.join('pages', 'permissions.py'), [
        (r'''    # by the login, superusers included.
    {'codename': 'can_access_wellness',       'edit_codename': None,                      'label': 'Wellness',              'icon': 'fa-spa'},
]

''',
         r'''    # by the login, superusers included.
    {'codename': 'can_access_wellness',       'edit_codename': None,                      'label': 'Wellness',              'icon': 'fa-spa'},
    # TR-1, 15 Nov 2026 - Travel. No edit tier, like Wellness: a trip is
    # its owner's, and shared ones are shared to change as well as see.
    {'codename': 'can_access_travel',         'edit_codename': None,                      'label': 'Travel',                'icon': 'fa-plane'},
]

'''),
    ]),
    (os.path.join('pages', 'middleware.py'), [
        (r'''            ('wellness', 'auth.can_access_wellness'),

            # ---------- RECIPES ----------
            ('recipe_management', 'auth.can_access_recipes'),
''',
         r'''            ('wellness', 'auth.can_access_wellness'),

            # ---------- TRAVEL (TR-1, 15 Nov 2026) ----------
            ('travel', 'auth.can_access_travel'),

            # ---------- RECIPES ----------
            ('recipe_management', 'auth.can_access_recipes'),
'''),
    ]),
    (os.path.join('pages', 'views', 'home.py'), [
        (r'''                'crs':          request.user.has_perm('auth.can_access_crs'),
                'wellness':     request.user.has_perm('auth.can_access_wellness'),
                # WL-1, 30 Oct 2026 - Wellness lives on Personal, so a
                # login with only Wellness still needs the way in.
''',
         r'''                'crs':          request.user.has_perm('auth.can_access_crs'),
                'wellness':     request.user.has_perm('auth.can_access_wellness'),
                'travel':       request.user.has_perm('auth.can_access_travel'),
                # WL-1, 30 Oct 2026 - Wellness lives on Personal, so a
                # login with only Wellness still needs the way in.
'''),
        (r'''                    or request.user.has_perm('auth.can_access_crs')
                    or request.user.has_perm('auth.can_access_wellness')
                ),
                'administration': request.user.has_perm('auth.can_access_administration'),
''',
         r'''                    or request.user.has_perm('auth.can_access_crs')
                    or request.user.has_perm('auth.can_access_wellness')
                    or request.user.has_perm('auth.can_access_travel')
                ),
                'administration': request.user.has_perm('auth.can_access_administration'),
'''),
    ]),
    (os.path.join('pages', 'views', 'administration.py'), [
        (r'''        # WL-1, 30 Oct 2026 - the fourth tile.
        'wellness':     request.user.has_perm('auth.can_access_wellness'),
    }
    return render(request, "personal.html", {
''',
         r'''        # WL-1, 30 Oct 2026 - the fourth tile.
        'wellness':     request.user.has_perm('auth.can_access_wellness'),
        # TR-1, 15 Nov 2026 - the fifth tile.
        'travel':       request.user.has_perm('auth.can_access_travel'),
    }
    return render(request, "personal.html", {
'''),
    ]),
    (os.path.join('pages', 'templates', 'base.html'), [
        (r'''      {% endif %}

      {% if user.is_superuser or perms.auth.can_access_passports or perms.auth.can_access_recipes or perms.auth.can_access_celebrations or perms.auth.can_access_crs or perms.auth.can_access_wellness %}
      <a href="{% url 'personal_page' %}" class="sidebar-link {% if request.resolver_match.url_name == 'personal_page' %}active{% endif %}" data-tooltip="Personal">
          <i class="fas fa-user-circle"></i><span class="link-text">Personal</span>
''',
         r'''      {% endif %}

      {% if user.is_superuser or perms.auth.can_access_passports or perms.auth.can_access_recipes or perms.auth.can_access_celebrations or perms.auth.can_access_crs or perms.auth.can_access_travel or perms.auth.can_access_wellness %}
      <a href="{% url 'personal_page' %}" class="sidebar-link {% if request.resolver_match.url_name == 'personal_page' %}active{% endif %}" data-tooltip="Personal">
          <i class="fas fa-user-circle"></i><span class="link-text">Personal</span>
'''),
        (r'''            {% endif %}
            {% if user.is_superuser or perms.auth.can_access_administration %}<li class="nav-item"><a class="nav-link" href="{% url 'admin_apms' %}">Administration</a></li>{% endif %}
            {% if user.is_superuser or perms.auth.can_access_passports or perms.auth.can_access_recipes or perms.auth.can_access_celebrations or perms.auth.can_access_crs or perms.auth.can_access_wellness %}<li class="nav-item"><a class="nav-link" href="{% url 'personal_page' %}">Personal</a></li>{% endif %}
            <li class="nav-item"><a class="nav-link" href="{% url 'help_page' %}"><i class="fas fa-question-circle"></i> Help</a></li>
          {% endif %}
''',
         r'''            {% endif %}
            {% if user.is_superuser or perms.auth.can_access_administration %}<li class="nav-item"><a class="nav-link" href="{% url 'admin_apms' %}">Administration</a></li>{% endif %}
            {% if user.is_superuser or perms.auth.can_access_passports or perms.auth.can_access_recipes or perms.auth.can_access_celebrations or perms.auth.can_access_crs or perms.auth.can_access_travel or perms.auth.can_access_wellness %}<li class="nav-item"><a class="nav-link" href="{% url 'personal_page' %}">Personal</a></li>{% endif %}
            <li class="nav-item"><a class="nav-link" href="{% url 'help_page' %}"><i class="fas fa-question-circle"></i> Help</a></li>
          {% endif %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'personal.html'), [
        (r'''      {% endif %}

      {% if perms_map.recipes %}
      <!-- Recipes -->
''',
         r'''      {% endif %}

      {% if perms_map.travel %}
      <!-- Travel - TR-1, 15 Nov 2026. Its own app at /travel/. Beside
           Passports: Demetri, 15 Nov - "Travel sits next to Passports". -->
      <a href="{% url 'travel:trips' %}" class="admin-btn btn-personal">
        <i class="fas fa-plane"></i>
        <h6>Travel</h6>
      </a>
      {% endif %}

      {% if perms_map.recipes %}
      <!-- Recipes -->
'''),
        (r'''
      {% if perms_map.wellness %}
      <!-- Wellness - WL-1, 30 Oct 2026. The fourth tile; the module
           behind it is its own app at /wellness/. -->
      <a href="{% url 'wellness:today' %}" class="admin-btn btn-personal">
        <i class="fas fa-spa"></i>
        <h6>Wellness</h6>
''',
         r'''
      {% if perms_map.wellness %}
      <!-- Wellness - WL-1, 30 Oct 2026. Its own app at /wellness/.
           TR-1, 15 Nov 2026: across the bottom, full width - the grid
           stays even with five tiles. -->
      <a href="{% url 'wellness:today' %}" class="admin-btn btn-personal admin-btn-wide">
        <i class="fas fa-spa"></i>
        <h6>Wellness</h6>
'''),
        (r'''
  /* Coming-soon tile is non-interactive */
  .admin-btn.coming-soon {
    opacity: 0.5;
''',
         r'''
  /* Coming-soon tile is non-interactive */
  /* TR-1, 15 Nov 2026 - Wellness across the bottom of the Personal grid. */
  .admin-grid .admin-btn-wide { grid-column: 1 / -1; }
  .admin-btn.coming-soon {
    opacity: 0.5;
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''  </article>

</section>

''',
         r'''  </article>

</section>

<!-- TR-1, 15 Nov 2026 - Travel, stage 1: trips, bookings, sharing, costs in two currencies. -->
<section data-module-slug="travel"
         data-module-group="Personal"
         data-module-permission="can_access_travel"
         data-module-name="Travel"
         data-module-icon="fa-plane"
         data-module-category="Personal"
         data-module-subtitle="Your trips, every booking in them, what they cost and what is still to pay">

  <article data-tab-slug="tr-overview"
           data-tab-name="Overview"
           data-tab-icon="fa-info-circle">
    <h6><i class="fas fa-plane"></i> Travel</h6>
    <p>Open <strong>Personal &rarr; Travel</strong> (beside Passports / Documents). Each trip holds its bookings &mdash; flights, stays, car hire, trains, ferries, transfers, activities &mdash; with every detail: the reference, dates and times, addresses, phone numbers, the cost, and whether it is paid. Attach the ticket or confirmation to each one.</p>
    <p>The list shows <strong>Upcoming</strong> trips first. Use the chips to see <strong>Past</strong> trips, one year, or one country. Each card shows the total, what is paid and what is still to pay.</p>
    <p>Coming next: bookings read straight from your forwarded emails, an itinerary and wish list, and a Travel app for your phone with your boarding passes.</p>
  </article>

  <article data-tab-slug="tr-trips"
           data-tab-name="Trips &amp; Sharing"
           data-tab-icon="fa-share-alt">
    <h6><i class="fas fa-share-alt"></i> Trips and sharing</h6>
    <p><strong>New trip</strong>: give it a name, and if you like its dates and countries. Leave the dates empty and they follow the bookings.</p>
    <p>A trip is <strong>yours alone</strong> until you share it. <strong>Share</strong> it, like a meal plan, with anyone who has Travel: they see the whole trip &mdash; bookings, documents and all the costs &mdash; and can add and change bookings. Only you, the owner, can change who it is shared with or delete the trip.</p>
  </article>

  <article data-tab-slug="tr-bookings"
           data-tab-name="Bookings"
           data-tab-icon="fa-ticket-alt">
    <h6><i class="fas fa-ticket-alt"></i> Bookings</h6>
    <p>On a trip, <strong>Add booking</strong>. Choose the kind, name it (&ldquo;TAP TP 1307&rdquo;, &ldquo;Casa do Largo&rdquo;), and fill in what you have: who it is with, the booking reference, when it starts and ends, from and to, the address, the phone number and the manage-booking link. Times are the local times on the booking.</p>
    <p>The trip page lists bookings by day. Open one to see everything about it, with a Map link for the address and the phone number ready to call. Under <strong>Tickets &amp; documents</strong> attach PDFs or pictures (up to 15 MB each); only the people on the trip can open them.</p>
    <p>Set <strong>Free cancellation until</strong> and <strong>Pay the balance by</strong>, and they show under <strong>Coming up</strong> on the trip.</p>
    <p><strong>No duplicates.</strong> Add a booking whose reference is already on the trip and you are stopped, with a link to the one it matches &mdash; change that one, or choose <strong>Save it as a second booking</strong>. Every change to a booking is kept: open <strong>Changes</strong> on the booking to see what changed, when and by whom; the booking itself always shows the latest.</p>
  </article>

  <article data-tab-slug="tr-costs"
           data-tab-name="Costs &amp; Currencies"
           data-tab-icon="fa-euro-sign">
    <h6><i class="fas fa-euro-sign"></i> Costs in two currencies</h6>
    <p>Enter a cost in the currency you paid in. It is kept as it is, and shown in euros as well, at the European Central Bank&rsquo;s reference rate for the day it was entered. The rate is stored with the booking, so the euro figure never moves.</p>
    <p>Paid in another currency by card? Type the euro amount from your statement into <strong>In euros</strong> &mdash; it replaces the estimate. If the rate cannot be fetched at that moment, the booking says <em>rate pending</em> and it is tried again the next time you open the trip.</p>
    <p>Mark each booking <strong>Paid</strong>, <strong>Part paid</strong> (with how much) or <strong>To pay</strong>. The <strong>Costs</strong> tab shows the total, what is paid, what is still to pay, and the spend by kind.</p>
  </article>
</section>

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
    raise SystemExit('TR-1 REFUSED: %s' % msg)


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
    if "'test_travel_one.py'" in read(pq):
        print('TR-1 already applied.')
        return 0
    if "'test_gift_tidy.py'" not in read(pq):
        refuse('Release 81 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'travel folder and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('TR-1 --check: %d file(s) would change, none written; %d '
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
    print('TR-1 applied - Travel, stage 1. Now run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
