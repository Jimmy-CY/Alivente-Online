# -*- coding: utf-8 -*-
"""apply_travel_six.py - round TR-6, 16 Nov 2026.

RELEASE 87 - A STAY'S COST ONCE, ON THE ITINERARY; "+ THINGS TO DO".

Demetri, 16 Nov: "I don't think that we should have the cost (e.g. for
PAREA 270.28) showing three times for three nights. This is the total for
the 3 nights, and this looks deceiving." On the itinerary a stay's (and a
car's) cost is on the day it starts, "for N nights"; the days between say
"Night 2 of 3"; the last day gives the check-out time, not the check-in. And "Add a
place" is now "+ Things to do" (Demetri: "+ Things to do works for me").

New files ship beside this patcher. Stands on Release 86. Idempotent.
Edits backed up to .bak_travel6. No migration.
"""
import os
import sys

SUFFIX = '.bak_travel6'
MARK = 'TR-6, 16 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_travel_six.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    # TR-5, 16 Nov 2026 - Release 86: Travel - restaurants, the wish list
    # matched to bookings, one PDF button, countries without home.
    'test_travel_five.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    # TR-5, 16 Nov 2026 - Release 86: Travel - restaurants, the wish list
    # matched to bookings, one PDF button, countries without home.
    'test_travel_five.py',
    # TR-6, 16 Nov 2026 - Release 87: a stay's cost once on the itinerary.
    'test_travel_six.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # TR-5, 16 Nov 2026 - Release 86: Travel - restaurants, and the review.
    '.bak_travel5',
]

''',
         r'''    # TR-5, 16 Nov 2026 - Release 86: Travel - restaurants, and the review.
    '.bak_travel5',
    # TR-6, 16 Nov 2026 - Release 87: a stay's cost once on the itinerary.
    '.bak_travel6',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''           data-tab-icon="fa-map-marker-alt">
    <h6><i class="fas fa-map-marker-alt"></i> The itinerary, things to do and places</h6>
    <p><strong>Add a place</strong> for somewhere with no booking &mdash; a museum, a garden, a restaurant, a viewpoint. Type its name or paste a Google Maps or website link. Claude looks it up on the web and fills in its proper name, the address, opening hours, price and website, usually within half a minute (the page refreshes by itself). The name can be short, lower case or misspelled &mdash; &ldquo;sagrada familia&rdquo; finds the Basilica de la Sagrada Familia, wherever the trip is going. If <strong>two or three places</strong> could be meant (a common name, a chain), it asks <strong>Which one did you mean?</strong> &mdash; pick one and that one is looked up, or <strong>None of these</strong> to keep it as you typed it. If nothing comes up, add the town to the name and press <strong>Try again</strong>. Check the hours before you go; anything you type wins over what was found. On the phone, in Google Maps, tap <strong>Share &rarr; Travel</strong> on a place and it opens Add a place for the trip you are on (or the next one).</p>
    <p>A place goes on a <strong>day</strong> (with a time if you like) or in the trip&rsquo;s <strong>Things to do</strong> &mdash; places with no day yet, which are also listed at the bottom of the <strong>Itinerary</strong> and of the PDF. In Things to do, <em>Put on</em>: choose the day (a time is optional), then <strong>Move</strong> &mdash; Move does nothing until a day is chosen. Each place has its buttons, and resting the pointer on one says what it does: <strong>Edit</strong> (change it, look it up again, remove it), <strong>Map</strong>, <strong>Back to Things to do</strong> (for a place on a day) and <strong>Done</strong>. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
  </article>
''',
         r'''           data-tab-icon="fa-map-marker-alt">
    <h6><i class="fas fa-map-marker-alt"></i> The itinerary, things to do and places</h6>
    <p><strong>+ Things to do</strong> adds somewhere with no booking &mdash; a museum, a garden, a restaurant, a viewpoint. Type its name or paste a Google Maps or website link. Claude looks it up on the web and fills in its proper name, the address, opening hours, price and website, usually within half a minute (the page refreshes by itself). The name can be short, lower case or misspelled &mdash; &ldquo;sagrada familia&rdquo; finds the Basilica de la Sagrada Familia, wherever the trip is going. If <strong>two or three places</strong> could be meant (a common name, a chain), it asks <strong>Which one did you mean?</strong> &mdash; pick one and that one is looked up, or <strong>None of these</strong> to keep it as you typed it. If nothing comes up, add the town to the name and press <strong>Try again</strong>. Check the hours before you go; anything you type wins over what was found. On the phone, in Google Maps, tap <strong>Share &rarr; Travel</strong> on a place and it opens <strong>+ Things to do</strong> for the trip you are on (or the next one).</p>
    <p>A place goes on a <strong>day</strong> (with a time if you like) or in the trip&rsquo;s <strong>Things to do</strong> &mdash; places with no day yet, which are also listed at the bottom of the <strong>Itinerary</strong> and of the PDF. In Things to do, <em>Put on</em>: choose the day (a time is optional), then <strong>Move</strong> &mdash; Move does nothing until a day is chosen. Each place has its buttons, and resting the pointer on one says what it does: <strong>Edit</strong> (change it, look it up again, remove it), <strong>Map</strong>, <strong>Back to Things to do</strong> (for a place on a day) and <strong>Done</strong>. The <strong>Itinerary</strong> tab shows every day of the trip with its bookings (check-ins, flights, the car) and its places in time order &mdash; a hotel&rsquo;s cost is shown once, on the check-in day, as the total for all its nights; the days after say which night it is and, on the last, the check-out time; places without a time come last. Tick a place <strong>Done</strong> when you have been. Everyone on the trip sees and can change its places.</p>
    <p>Today on the phone shows today&rsquo;s and tomorrow&rsquo;s places along with the bookings.</p>
  </article>
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''        b.when = '' if what == 'during' else (
            (b.start_time if what == 'start' else b.end_time) or '')
        out.append(b)
    return out
''',
         r'''        b.when = '' if what == 'during' else (
            (b.start_time if what == 'start' else b.end_time) or '')
        # TR-6, 16 Nov 2026 - which night of the stay this is (Demetri:
        # the stay's cost on all three days "looks deceiving").
        b.nights = (b.end_date - b.start_date).days \
            if b.kind == 'stay' and b.start_date and b.end_date else None
        b.night = (day - b.start_date).days + 1 \
            if what == 'during' and b.nights else None
        out.append(b)
    return out
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_booking_row.html'), [
        (r'''<a href="{% url 'travel:booking' b.pk %}" class="tv-bk{% if b.cancelled %} tv-off{% endif %}" data-booking>
    <span class="tv-ico" title="{{ b.kind_label }}"><i class="fas {{ b.icon }}" aria-hidden="true"></i></span>
    <span><b>{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag tv-due">Cancelled</span>{% endif %}<span class="tv-sub" style="display: block">{% if b.start_time %}{{ b.start_time|time:"H:i" }}{% if b.end_time and b.end_date == b.start_date %} → {{ b.end_time|time:"H:i" }}{% endif %} · {% endif %}{% if b.route %}{{ b.route }} · {% endif %}{% if b.kind == 'stay' and b.end_date %}until {{ b.end_date|date:"D j M" }} · {% endif %}{% if b.reference %}ref {{ b.reference }}{% endif %}{% if b.who %} · {{ b.who }}{% endif %}</span>{% if b.kind == 'stay' or b.kind == 'restaurant' %}{% if b.address or b.phone %}{% if b.what != 'during' %}{% comment %} TR-5 (Demetri, 16 Nov): a hotel's or restaurant's address and phone, on the day. {% endcomment %}<span class="tv-detail" data-row-detail>{% if b.address %}{{ b.address }}{% endif %}{% if b.address and b.phone %} · {% endif %}{% if b.phone %}{{ b.phone }}{% endif %}{% if b.kind == 'stay' and b.what == 'start' and b.end_time %} · check out by {{ b.end_time|time:"H:i" }}{% endif %}</span>{% endif %}{% endif %}{% endif %}</span>
    <span class="tv-amt">{% if b.amount is not None %}<b>{{ b.eur_label|default:"rate pending" }}</b>{% if b.orig_label %}<span class="tv-orig" style="display: block">{{ b.orig_label }}</span>{% endif %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% elif b.included %}<span class="tv-sub small" data-included>Included in {{ b.included.segment|default:b.included.title }}</span>{% endif %}</span>
</a>
''',
         r'''{% comment %} One booking as a row. TR-6, 16 Nov 2026 (Demetri: "I don't think that we should have the cost (e.g. for PAREA 270.28) showing three times for three nights. This is the total for the 3 nights, and this looks deceiving"): on the itinerary a stay's or a car's cost is on the day it starts only; the days after say which night it is, or the check-out time. {% endcomment %}<a href="{% url 'travel:booking' b.pk %}" class="tv-bk{% if b.cancelled %} tv-off{% endif %}" data-booking>
    <span class="tv-ico" title="{{ b.kind_label }}"><i class="fas {{ b.icon }}" aria-hidden="true"></i></span>
    <span><b>{% if b.label %}{{ b.label }}: {% endif %}{{ b.title }}</b>{% if b.cancelled %} <span class="tv-tag tv-due">Cancelled</span>{% endif %}<span class="tv-sub" style="display: block">{% if b.what == 'during' %}{% if b.night %}Night {{ b.night }} of {{ b.nights }} · {% endif %}until {{ b.end_date|date:"D j M" }}{% if b.reference %} · ref {{ b.reference }}{% endif %}{% elif b.what == 'end' %}{% if b.kind == 'stay' %}Check out{% else %}Drop off{% endif %}{% if b.end_time %} by {{ b.end_time|time:"H:i" }}{% endif %}{% if b.reference %} · ref {{ b.reference }}{% endif %}{% else %}{% if b.start_time %}{{ b.start_time|time:"H:i" }}{% if b.end_time and b.end_date == b.start_date %} → {{ b.end_time|time:"H:i" }}{% endif %} · {% endif %}{% if b.route %}{{ b.route }} · {% endif %}{% if b.kind == 'stay' and b.end_date %}until {{ b.end_date|date:"D j M" }} · {% endif %}{% if b.reference %}ref {{ b.reference }}{% endif %}{% if b.who %} · {{ b.who }}{% endif %}{% endif %}</span>{% if b.kind == 'stay' or b.kind == 'restaurant' %}{% if b.address or b.phone %}{% if b.what != 'during' %}{% comment %} TR-5 (Demetri, 16 Nov): a hotel's or restaurant's address and phone, on the day. {% endcomment %}<span class="tv-detail" data-row-detail>{% if b.address %}{{ b.address }}{% endif %}{% if b.address and b.phone %} · {% endif %}{% if b.phone %}{{ b.phone }}{% endif %}{% if b.kind == 'stay' and b.what == 'start' and b.end_time %} · check out by {{ b.end_time|time:"H:i" }}{% endif %}</span>{% endif %}{% endif %}{% endif %}</span>
    <span class="tv-amt">{% if b.what == 'during' or b.what == 'end' %}{% elif b.amount is not None %}<b>{{ b.eur_label|default:"rate pending" }}</b>{% if b.orig_label %}<span class="tv-orig" style="display: block">{{ b.orig_label }}</span>{% endif %}{% if b.nights and b.what == 'start' %}<span class="tv-orig" style="display: block" data-stay-total>for {{ b.nights }} night{{ b.nights|pluralize }}</span>{% endif %}<span class="tv-tag {% if b.paid == 'paid' %}tv-paid{% else %}tv-due{% endif %}">{{ b.status_label }}</span>{% elif b.included %}<span class="tv-sub small" data-included>Included in {{ b.included.segment|default:b.included.title }}</span>{% endif %}</span>
</a>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'trip.html'), [
        (r'''<div class="page-action-buttons">
    <a href="{% url 'travel:booking_new' trip.pk %}" class="btn action-primary"><i class="fas fa-plus"></i> Add booking</a>
    <a href="{% url 'travel:place_new' trip.pk %}" class="btn action-secondary"><i class="fas fa-map-marker-alt"></i> Add a place</a>
    {% if is_owner %}<a href="{% url 'travel:trip_share' trip.pk %}" class="btn action-secondary"><i class="fas fa-share-alt"></i> Share</a>{% endif %}
    <a href="{% url 'travel:trip_edit' trip.pk %}" class="btn action-secondary"><i class="fas fa-pen"></i> Edit trip</a>
''',
         r'''<div class="page-action-buttons">
    <a href="{% url 'travel:booking_new' trip.pk %}" class="btn action-primary"><i class="fas fa-plus"></i> Add booking</a>
    <a href="{% url 'travel:place_new' trip.pk %}" class="btn action-secondary"><i class="fas fa-plus"></i> Things to do</a>
    {% if is_owner %}<a href="{% url 'travel:trip_share' trip.pk %}" class="btn action-secondary"><i class="fas fa-share-alt"></i> Share</a>{% endif %}
    <a href="{% url 'travel:trip_edit' trip.pk %}" class="btn action-secondary"><i class="fas fa-pen"></i> Edit trip</a>
'''),
        (r'''    {% for day, rows in itinerary %}
    <section class="form-card tv-day" id="d{{ day|date:'Ymd' }}" data-itinerary-day>
        <div class="tv-row"><h3>{{ day|date:"l j F" }}</h3><a href="{% url 'travel:place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}" class="small"><i class="fas fa-plus" aria-hidden="true"></i> Add a place</a></div>
        {% for r in rows %}{% if r.is_place %}{% include 'travel/_place_row.html' with p=r %}{% else %}{% include 'travel/_booking_row.html' with b=r %}{% endif %}{% empty %}<p class="tv-sub small" style="margin: 0">Nothing planned{% if wish %} &mdash; move something here from the <a href="{% url 'travel:trip_wishlist' trip.pk %}">things to do</a>{% endif %}.</p>{% endfor %}
    </section>
''',
         r'''    {% for day, rows in itinerary %}
    <section class="form-card tv-day" id="d{{ day|date:'Ymd' }}" data-itinerary-day>
        <div class="tv-row"><h3>{{ day|date:"l j F" }}</h3><a href="{% url 'travel:place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}" class="small"><i class="fas fa-plus" aria-hidden="true"></i> Things to do</a></div>
        {% for r in rows %}{% if r.is_place %}{% include 'travel/_place_row.html' with p=r %}{% else %}{% include 'travel/_booking_row.html' with b=r %}{% endif %}{% empty %}<p class="tv-sub small" style="margin: 0">Nothing planned{% if wish %} &mdash; move something here from the <a href="{% url 'travel:trip_wishlist' trip.pk %}">things to do</a>{% endif %}.</p>{% endfor %}
    </section>
'''),
        (r'''    {% comment %} TR-4 - places with no day yet. {% endcomment %}
    <section class="form-card" data-wishlist>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Things to do</h3><a href="{% url 'travel:place_new' trip.pk %}" class="btn action-primary btn-sm"><i class="fas fa-plus"></i> Add a place</a></div>
        {% for p in wish %}
        <div data-wish-item>
''',
         r'''    {% comment %} TR-4 - places with no day yet. {% endcomment %}
    <section class="form-card" data-wishlist>
        <div class="tv-row"><h3 class="form-section-title" style="margin: 0">Things to do</h3><a href="{% url 'travel:place_new' trip.pk %}" class="btn action-primary btn-sm"><i class="fas fa-plus"></i> Things to do</a></div>
        {% for p in wish %}
        <div data-wish-item>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'place_form.html'), [
        (r'''{% extends 'base.html' %}
{% load help_modal_tags %}
{% block title %}{% if p %}{{ p.name }}{% else %}Add a place{% endif %} - Travel{% endblock %}
{% comment %} TRAVEL - TR-4, 15 Nov 2026. Add a place (a name, a link, or what Google Maps shared) - Claude looks it up - or change one. {% endcomment %}
{% block content %}
{% include 'travel/_style.html' %}
{% if p and p.lookup == 'waiting' %}<meta http-equiv="refresh" content="5">{% endif %}
<h2 class="page-title-h2">TRAVEL</h2>
<h4 class="page-subtitle-h4">{% if p %}{{ p.name|upper }}{% else %}ADD A PLACE &middot; {{ trip.name|upper }}{% endif %}</h4>
<div class="page-action-buttons">
    {% if p %}<a href="{{ p.map_url }}" target="_blank" rel="noopener" class="btn action-secondary"><i class="fas fa-map"></i> Map</a>{% if p.website %}<a href="{{ p.website }}" target="_blank" rel="noopener" class="btn action-secondary"><i class="fas fa-globe"></i> Website</a>{% endif %}{% endif %}
''',
         r'''{% extends 'base.html' %}
{% load help_modal_tags %}
{% block title %}{% if p %}{{ p.name }}{% else %}Things to do{% endif %} - Travel{% endblock %}
{% comment %} TRAVEL - TR-4, 15 Nov 2026. Add a place (a name, a link, or what Google Maps shared) - Claude looks it up - or change one. {% endcomment %}
{% block content %}
{% include 'travel/_style.html' %}
{% if p and p.lookup == 'waiting' %}<meta http-equiv="refresh" content="5">{% endif %}
<h2 class="page-title-h2">TRAVEL</h2>
<h4 class="page-subtitle-h4">{% if p %}{{ p.name|upper }}{% else %}THINGS TO DO &middot; {{ trip.name|upper }}{% endif %}</h4>
<div class="page-action-buttons">
    {% if p %}<a href="{{ p.map_url }}" target="_blank" rel="noopener" class="btn action-secondary"><i class="fas fa-map"></i> Map</a>{% if p.website %}<a href="{{ p.website }}" target="_blank" rel="noopener" class="btn action-secondary"><i class="fas fa-globe"></i> Website</a>{% endif %}{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'place.html'), [
        (r'''{% extends 'travel/m/base.html' %}
{% comment %} TR-4 - Add a place on the phone (typed, pasted, or shared from Google Maps), or one place: what is known, where it goes. {% endcomment %}
{% block title %}{% if p %}{{ p.name }}{% else %}Add a place{% endif %} - Travel{% endblock %}
{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trip' trip.pk %}?tab={% if p and p.day %}itinerary{% else %}wish{% endif %}"><span aria-hidden="true">‹</span> {{ trip.name }}</a><h1>{% if p %}{{ p.name }}{% else %}Add a place{% endif %}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if p %}{% if p.day %}{{ p.day|date:"D j M" }}{% if p.time %} · {{ p.time|time:"H:i" }}{% endif %}{% else %}In Things to do{% endif %}{% else %}No booking needed · museums, gardens, restaurants{% endif %}</div>{% endblock %}
{% block content %}
''',
         r'''{% extends 'travel/m/base.html' %}
{% comment %} TR-4 - Add a place on the phone (typed, pasted, or shared from Google Maps), or one place: what is known, where it goes. {% endcomment %}
{% block title %}{% if p %}{{ p.name }}{% else %}Things to do{% endif %} - Travel{% endblock %}
{% block top %}<div style="min-width: 0"><a class="tv-back" href="{% url 'travel:m_trip' trip.pk %}?tab={% if p and p.day %}itinerary{% else %}wish{% endif %}"><span aria-hidden="true">‹</span> {{ trip.name }}</a><h1>{% if p %}{{ p.name }}{% else %}Things to do{% endif %}</h1></div>{% endblock %}
{% block sub %}<div class="sub">{% if p %}{% if p.day %}{{ p.day|date:"D j M" }}{% if p.time %} · {{ p.time|time:"H:i" }}{% endif %}{% else %}In Things to do{% endif %}{% else %}No booking needed · museums, gardens, restaurants{% endif %}</div>{% endblock %}
{% block content %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'trip.html'), [
        (r'''{% if sub == 'itinerary' %}
{% comment %} TR-4 - the itinerary: every day, bookings and places in time order. {% endcomment %}
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Add a place</a>
{% if itinerary %}
<nav class="tv-chips" aria-label="Days" style="flex-wrap: nowrap; overflow-x: auto">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}" style="flex: none">{{ day|date:"D j" }}</a>{% endfor %}</nav>
{% for day, rows in itinerary %}
<p class="tv-h3" id="d{{ day|date:'Ymd' }}">{{ day|date:"l j F" }}</p>
<section class="tv-card" data-itinerary-day>{% for b in rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing planned. <a href="{% url 'travel:m_place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}">Add a place</a></p>{% endfor %}</section>
{% endfor %}
{% comment %} TR-5 - what is not on a day yet, at the bottom of the itinerary. {% endcomment %}
''',
         r'''{% if sub == 'itinerary' %}
{% comment %} TR-4 - the itinerary: every day, bookings and places in time order. {% endcomment %}
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Things to do</a>
{% if itinerary %}
<nav class="tv-chips" aria-label="Days" style="flex-wrap: nowrap; overflow-x: auto">{% for day, rows in itinerary %}<a class="tv-chip" href="#d{{ day|date:'Ymd' }}" style="flex: none">{{ day|date:"D j" }}</a>{% endfor %}</nav>
{% for day, rows in itinerary %}
<p class="tv-h3" id="d{{ day|date:'Ymd' }}">{{ day|date:"l j F" }}</p>
<section class="tv-card" data-itinerary-day>{% for b in rows %}{% include 'travel/m/_row.html' %}{% empty %}<p class="tv-muted" style="margin: 0">Nothing planned. <a href="{% url 'travel:m_place_new' trip.pk %}?day={{ day|date:'Y-m-d' }}">+ Things to do</a></p>{% endfor %}</section>
{% endfor %}
{% comment %} TR-5 - what is not on a day yet, at the bottom of the itinerary. {% endcomment %}
'''),
        (r'''{% elif sub == 'wish' %}
{% comment %} TR-4 - Things to do: places with no day yet. {% endcomment %}
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Add a place</a>
{% for p in wish %}
<section class="tv-card" data-wish-item>
''',
         r'''{% elif sub == 'wish' %}
{% comment %} TR-4 - Things to do: places with no day yet. {% endcomment %}
<a href="{% url 'travel:m_place_new' trip.pk %}" class="tv-btn wide" data-add-place>+ Things to do</a>
{% for p in wish %}
<section class="tv-card" data-wish-item>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Every boarding pass to come, one a screen &mdash; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed, the next flight&rsquo;s pass is the one on screen, and earlier ones are a swipe back. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. Add a place by name (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
{% endblock %}
''',
         r'''<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Every boarding pass to come, one a screen &mdash; swipe for the next person&rsquo;s. It always opens on the next pass you need: once a flight has landed, the next flight&rsquo;s pass is the one on screen, and earlier ones are a swipe back. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
<section class="tv-card"><p class="tv-h2">Getting bookings in</p><p style="margin: 0">Forward the booking email to <b>{{ address }}</b>, or on Android use <b>Share &rarr; Travel</b> on an email, a PDF ticket or a screenshot. It is read in a minute and waits under <b>To check</b>. A later email about a booking you have updates it by itself.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
<section class="tv-card"><p class="tv-h2">Changing things</p><p style="margin: 0">Add, edit, share and merge trips on the full site, under Personal &rarr; Travel. The phone is for the trip itself.</p></section>
{% endblock %}
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
    raise SystemExit('TR-6 REFUSED: %s' % msg)


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
    if "'test_travel_six.py'" in read(pq):
        print('TR-6 already applied.')
        return 0
    if "'test_travel_five.py'" not in read(pq):
        refuse('Release 86 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new travel files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('TR-6 --check: %d file(s) would change, none written; %d '
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
    print('TR-6 applied - a stay\'s cost once on the itinerary. No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
