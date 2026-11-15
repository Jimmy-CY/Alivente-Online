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
