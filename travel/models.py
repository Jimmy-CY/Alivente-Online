# -*- coding: utf-8 -*-
"""travel/models.py - TR-1, 15 Nov 2026. Trips, their bookings, the files
that came with them, and the euro rates the costs were converted at."""
import os
import uuid
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q


class Trip(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='trips')
    name = models.CharField(max_length=120)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    # Free text, comma separated, as the person writes them: "Portugal",
    # "Greece, Ireland".
    countries = models.CharField(max_length=200, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    shared_with = models.ManyToManyField(User, blank=True,
                                         related_name='shared_trips')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'travel_trips'
        ordering = ['-start_date', '-id']

    def __str__(self):
        return self.name

    @property
    def country_list(self):
        return [c.strip() for c in self.countries.split(',') if c.strip()]

    def can_see(self, user):
        return self.owner_id == user.id or \
            self.shared_with.filter(pk=user.pk).exists()


def trips_for(user):
    """Every trip this person may open: their own and those shared with
    them. The ONE door - views never look a trip up any other way."""
    return Trip.objects.filter(Q(owner=user) | Q(shared_with=user)).distinct()


class Booking(models.Model):
    KINDS = [
        ('flight', 'Flight'),
        ('stay', 'Stay'),
        ('car', 'Car hire'),
        ('train', 'Train'),
        ('ferry', 'Ferry'),
        ('transfer', 'Transfer'),
        ('activity', 'Activity'),
        # TR-5, 16 Nov 2026 - a table booked at a restaurant (Demetri:
        # "Let's do a Restaurant type"), from the restaurant, TheFork or
        # OpenTable.
        ('restaurant', 'Restaurant'),
        ('other', 'Other'),
    ]
    PAID = [
        ('paid', 'Paid'),
        ('part', 'Part paid'),
        ('due', 'To pay'),
    ]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='bookings')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name='+')
    kind = models.CharField(max_length=12, choices=KINDS, default='other')
    title = models.CharField(max_length=160)
    provider = models.CharField(max_length=120, blank=True, default='')
    reference = models.CharField(max_length=60, blank=True, default='')
    # Local times at the place, as the booking states them - no time zone
    # arithmetic, so 06:40 in Larnaca stays 06:40.
    start_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    from_place = models.CharField(max_length=120, blank=True, default='')
    to_place = models.CharField(max_length=120, blank=True, default='')
    address = models.CharField(max_length=255, blank=True, default='')
    phone = models.CharField(max_length=40, blank=True, default='')
    link = models.URLField(max_length=500, blank=True, default='')
    details = models.TextField(blank=True, default='')
    # THE COST, IN TWO CURRENCIES (Demetri, 15 Nov: "the original currency,
    # but also a conversion to Euros"). amount_eur is either converted at
    # fx_rate (units of `currency` per euro, as the ECB quotes it) on
    # fx_date, or typed - eur_typed - from the card statement.
    currency = models.CharField(max_length=3, default='EUR')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True,
                                 blank=True)
    amount_eur = models.DecimalField(max_digits=10, decimal_places=2,
                                     null=True, blank=True)
    fx_rate = models.DecimalField(max_digits=14, decimal_places=6, null=True,
                                  blank=True)
    fx_date = models.DateField(null=True, blank=True)
    eur_typed = models.BooleanField(default=False)
    paid = models.CharField(max_length=4, choices=PAID, default='due')
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                      null=True, blank=True)
    pay_by = models.DateField(null=True, blank=True)
    cancel_until = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=10, default='manual')
    # TR-2, 15 Nov 2026 - read from emails. A cancellation marks a booking
    # Cancelled rather than deleting it (Demetri's rule); it stays on the
    # trip, struck through, and out of the totals.
    STATUSES = [('ok', 'Booked'), ('cancelled', 'Cancelled')]
    status = models.CharField(max_length=10, choices=STATUSES, default='ok')
    # One part of a booking that has several under one reference - a
    # flight number ("CY 326") or a leg ("LCA-ATH"). Two flights on one
    # booking reference are two bookings; this tells them apart.
    segment = models.CharField(max_length=40, blank=True, default='')
    # The Date of the latest email applied. An older email arriving later
    # (forwarded out of order) never overwrites what a newer one said.
    email_date = models.DateTimeField(null=True, blank=True)
    # A boarding pass: the barcode's own text (BCBP for a flight) and its
    # symbology, kept for the Travel phone app to draw; the airline's own
    # wallet link where the email had one.
    pass_code = models.TextField(blank=True, default='')
    pass_format = models.CharField(max_length=12, blank=True, default='')
    wallet_link = models.URLField(max_length=1000, blank=True, default='')
    # WHO IS TRAVELLING (Demetri, 15 Nov). People with Travel, ticked; and
    # names from an email that matched nobody, kept as written.
    travellers = models.ManyToManyField(User, blank=True,
                                        related_name='travel_bookings')
    traveller_names = models.CharField(max_length=255, blank=True,
                                       default='')
    # TR-4, 15 Nov 2026 - where it is, as the email said: the trip's
    # countries come from its bookings (Demetri: "Should the Trip Name and
    # the From and To Dates be based on uploaded reservations?").
    city = models.CharField(max_length=80, blank=True, default='')
    country = models.CharField(max_length=60, blank=True, default='')
    # TR-5, 16 Nov 2026 - when a stay's or a restaurant's missing details
    # (address, phone, check-in and check-out times) were last looked up
    # on the web (Demetri: "more details for like hotels (address, phone
    # number, check in and check out time, etc.)"). Once per booking.
    web_checked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'travel_bookings'
        ordering = ['start_date', 'start_time', 'id']

    def __str__(self):
        return self.title

    def eur_of(self, value):
        """A sum in this booking's currency, in euros (None if no rate)."""
        if value is None:
            return None
        if self.currency == 'EUR':
            return value
        if self.amount and self.amount_eur is not None:
            return (value * self.amount_eur / self.amount).quantize(
                Decimal('0.01'))
        return None

    @property
    def paid_eur(self):
        if self.paid == 'paid':
            return self.amount_eur
        if self.paid == 'part':
            return self.eur_of(self.paid_amount) or Decimal('0')
        return Decimal('0')

    @property
    def due_eur(self):
        if self.amount_eur is None:
            return None
        return self.amount_eur - (self.paid_eur or Decimal('0'))


def booking_file_path(instance, filename):
    # A random folder per file: these are tickets and passes, and /media/
    # is served without a login. The app serves them through
    # travel:file, which checks the trip.
    base = os.path.basename(filename)[-120:] or 'file'
    return 'travel/%s/%s' % (uuid.uuid4().hex, base)


class BookingFile(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE,
                                related_name='files')
    file = models.FileField(upload_to=booking_file_path, max_length=255)
    name = models.CharField(max_length=160)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'travel_booking_files'
        ordering = ['id']

    def __str__(self):
        return self.name


class FxRate(models.Model):
    """A euro reference rate, as the ECB published it for a day: `rate`
    units of `currency` buy one euro."""
    day = models.DateField()
    currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=14, decimal_places=6)

    class Meta:
        db_table = 'travel_fx_rates'
        unique_together = [('day', 'currency')]

    def __str__(self):
        return '%s %s %s' % (self.day, self.currency, self.rate)


class BookingChange(models.Model):
    """TR-1, 15 Nov 2026 - what changed on a booking, when, and who or what
    changed it. Demetri: when two or three emails come for one booking,
    "take the details of the latest email and show these ... have a place
    where somebody can click to view changes". The booking always holds the
    latest; this is the trail behind it. `changes` is a list of
    {"label", "old", "new"}."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE,
                                related_name='changes')
    when = models.DateTimeField(auto_now_add=True)
    by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                           blank=True, related_name='+')
    # 'edit' (typed on the page) or 'email' (stage 2: a later email).
    source = models.CharField(max_length=10, default='edit')
    note = models.CharField(max_length=200, blank=True, default='')
    changes = models.JSONField(default=list)

    class Meta:
        db_table = 'travel_booking_changes'
        ordering = ['-when', '-id']


# ==========================================================================
# TR-2, 15 Nov 2026 - STAGE 2: BOOKINGS READ FROM FORWARDED EMAILS.
#
# The road: a family member forwards a booking email to the trips address;
# Cloudflare hands it to the app (travel:inbound); the sender decides whose
# it is; Claude reads it; each booking in it becomes a CheckItem in that
# person's To check list - or, when it is a later email about a booking
# already on one of their trips, it updates that booking directly and the
# change trail says so.
# ==========================================================================
class TravelAddress(models.Model):
    """An email address someone forwards from, beyond their login email.
    An address belongs to one person only, and never to another user's
    login email."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='travel_addresses')
    email = models.EmailField(max_length=190, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'travel_addresses'
        ordering = ['email']

    def __str__(self):
        return self.email


def inbox_path(instance, filename):
    base = os.path.basename(filename)[-120:] or 'file'
    return 'travel/inbox/%s/%s' % (uuid.uuid4().hex, base)


class InboundEmail(models.Model):
    STATES = [('new', 'Waiting to be read'), ('reading', 'Being read'),
              ('done', 'Read'), ('failed', 'Could not be read'),
              ('ignored', 'Ignored')]
    received = models.DateTimeField(auto_now_add=True)
    # Unique, so the same email forwarded twice is taken once. Hashed when
    # longer than the column.
    message_id = models.CharField(max_length=190, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                             blank=True, related_name='+')
    sender = models.CharField(max_length=190, blank=True, default='')
    subject = models.CharField(max_length=255, blank=True, default='')
    sent = models.DateTimeField(null=True, blank=True)
    # Cloudflare's own check of the sender (SPF / DKIM / DMARC). An email
    # that did not pass changes nothing by itself - every booking in it
    # waits in To check.
    trusted = models.BooleanField(default=False)
    state = models.CharField(max_length=8, choices=STATES, default='new')
    started = models.DateTimeField(null=True, blank=True)
    tries = models.PositiveSmallIntegerField(default=0)
    note = models.CharField(max_length=255, blank=True, default='')
    # The email itself, only until it has been read. It can carry a PIN or
    # the last digits of a card, so it is deleted as soon as it is read.
    raw = models.FileField(upload_to=inbox_path, max_length=255, blank=True)

    class Meta:
        db_table = 'travel_inbound_emails'
        ordering = ['-received', '-id']

    def __str__(self):
        return self.subject or self.message_id


class InboundFile(models.Model):
    """A ticket, confirmation or pass that came attached to an email. It
    becomes a BookingFile (the same stored file) when its booking is
    added or updated."""
    email = models.ForeignKey(InboundEmail, on_delete=models.CASCADE,
                              related_name='files')
    file = models.FileField(upload_to=inbox_path, max_length=255)
    name = models.CharField(max_length=160)

    class Meta:
        db_table = 'travel_inbound_files'
        ordering = ['id']


class CheckItem(models.Model):
    """One booking read from an email, waiting for its person in To check.

    what:  new     - a booking not on any of your trips
           maybe   - no reference to go on, but it looks like one you have
           update  - a later email about a booking you have (held only
                     when the sender could not be confirmed)
           join    - it belongs with someone else's trip you are not on
           gmail   - Gmail asks to confirm forwarding to the trips address
           none    - the email had no booking in it
           failed  - the email could not be read
    """
    WHATS = ['new', 'maybe', 'update', 'join', 'gmail', 'none', 'failed']
    STATES = [('open', 'To check'), ('asked', 'Asked the owner'),
              ('done', 'Done'), ('dismissed', 'Dismissed')]
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='travel_checks')
    email = models.ForeignKey(InboundEmail, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='items')
    what = models.CharField(max_length=8, default='new')
    data = models.JSONField(default=dict)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='+')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True,
                             blank=True, related_name='+')
    other_trip = models.ForeignKey(Trip, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='+')
    state = models.CharField(max_length=10, choices=STATES, default='open')
    note = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'travel_check_items'
        ordering = ['-created_at', '-id']


class JoinRequest(models.Model):
    """THE OWNER IS ALWAYS ASKED (Demetri, 15 Nov: "An owner should be
    asked before merging" ... "or before somebody joins their trip").

    Either a person asks to join `trip` with a booking from their To check
    (item), or the owner of `trip` asks to merge `from_trip` - someone
    else's - into it. Nothing moves until the owner of the trip that gives
    something up says yes."""
    STATES = [('open', 'Waiting'), ('yes', 'Agreed'), ('no', 'Declined')]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='join_requests')
    by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    item = models.ForeignKey(CheckItem, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='requests')
    from_trip = models.ForeignKey(Trip, on_delete=models.CASCADE, null=True,
                                  blank=True, related_name='merge_requests')
    state = models.CharField(max_length=4, choices=STATES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'travel_join_requests'
        ordering = ['-created_at', '-id']

    @property
    def asks(self):
        """Who has to say yes: the owner of the trip that gives something
        up - the trip joined, or for a merge the trip merged away."""
        return self.from_trip.owner if self.from_trip_id else self.trip.owner


class BoardingPass(models.Model):
    """TR-3, 15 Nov 2026 - one passenger's boarding pass for one flight.

    A family flies on one booking reference, but each person has a pass of
    their own: Alexandra's must not overwrite Demetri's when her email
    comes in second. So the pass is its own row, one per passenger (the
    name the barcode itself carries), and Booking.pass_code keeps only the
    latest as stage 2 left it."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE,
                                related_name='passes')
    name = models.CharField(max_length=80, blank=True, default='')
    code = models.TextField()
    format = models.CharField(max_length=12, default='aztec')
    seat = models.CharField(max_length=8, blank=True, default='')
    wallet_link = models.URLField(max_length=1000, blank=True, default='')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'travel_boarding_passes'
        ordering = ['name', 'id']

    def __str__(self):
        return '%s %s' % (self.booking, self.name)


class Place(models.Model):
    """TR-4, 15 Nov 2026 - somewhere to go with no booking: a museum, a
    garden, a restaurant, a viewpoint. Typed, pasted as a link, or shared
    from Google Maps on the phone; Claude looks it up on the web for the
    address, hours, price and website. With a day it is on the itinerary;
    without one it is on the trip's wish list."""
    KINDS = [('sight', 'Sight'), ('museum', 'Museum'), ('food', 'Food & drink'),
             ('nature', 'Park & nature'), ('shop', 'Shopping'),
             ('activity', 'Activity'), ('other', 'Other')]
    LOOKUP = [('', 'Typed'), ('waiting', 'Looking it up'),
              ('found', 'Found'), ('failed', 'Not found'),
              # TR-5 - two or three places could be meant: the person
              # picks one (Demetri, 16 Nov: "if it finds two or three
              # options, then maybe the user must be given these options
              # to choose from").
              ('choose', 'Which one?')]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='places')
    name = models.CharField(max_length=160)
    kind = models.CharField(max_length=10, choices=KINDS, default='sight')
    address = models.CharField(max_length=255, blank=True, default='')
    website = models.URLField(max_length=500, blank=True, default='')
    maps_link = models.URLField(max_length=500, blank=True, default='')
    hours = models.CharField(max_length=255, blank=True, default='')
    price = models.CharField(max_length=120, blank=True, default='')
    about = models.CharField(max_length=300, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    day = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    done = models.BooleanField(default=False)
    query = models.CharField(max_length=500, blank=True, default='')
    lookup = models.CharField(max_length=8, choices=LOOKUP, blank=True,
                              default='')
    lookup_note = models.CharField(max_length=255, blank=True, default='')
    started = models.DateTimeField(null=True, blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name='+')
    # TR-5 - [{name, city, country, address, about}], at most three, while
    # lookup is 'choose'.
    options = models.JSONField(default=list, blank=True)
    # TR-5 - the booking that made it real: a table booked at a restaurant
    # on the wish list (Demetri: "Matching to the Wish List is
    # necessary"). It then sits on the booking's day and time and shows
    # once on the itinerary - as the booking.
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='places')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'travel_places'
        ordering = ['day', 'time', 'id']

    def __str__(self):
        return self.name

    @property
    def map_url(self):
        """The place on Google Maps: its own link, else a search."""
        if self.maps_link:
            return self.maps_link
        from urllib.parse import quote
        q = ', '.join(x for x in (self.name, self.address) if x)
        return 'https://www.google.com/maps/search/?api=1&query=' + quote(q)
