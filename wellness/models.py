# -*- coding: utf-8 -*-
"""wellness/models.py - WL-1, 30 Oct 2026.

Everything here hangs off a User. There is no workspace scoping and no
household pooling: a member logs in and sees their own Wellness, and only
theirs (decisions 1 and 2, 30 Oct 2026).
"""
from django.conf import settings
from django.db import models


class WellnessProfile(models.Model):
    """Per-person settings, made on the first visit."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='wellness_profile')
    # Welcome cards and starter set seen (the first-run flow).
    onboarded = models.BooleanField(default=False)
    # One-time tips already dismissed, as a list of tip keys.
    tips_seen = models.JSONField(default=list, blank=True)
    # WL-2, 30 Oct 2026 - Body. Height for the waist-to-height ratio; a
    # goal weight and an optional date for "on pace for".
    height_cm = models.DecimalField(max_digits=5, decimal_places=1,
                                    null=True, blank=True)
    weight_goal = models.DecimalField(max_digits=5, decimal_places=1,
                                      null=True, blank=True)
    goal_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wellness_profile'

    def __str__(self):
        return 'Wellness profile of %s' % self.user


class Habit(models.Model):
    KIND_YES_NO = 'yes_no'
    KIND_COUNT = 'count'
    KIND_DURATION = 'duration'
    KIND_AVOID = 'avoid'
    KINDS = [
        (KIND_YES_NO, 'Yes or no'),
        (KIND_COUNT, 'A count'),
        (KIND_DURATION, 'Minutes'),
        (KIND_AVOID, 'Something to avoid'),
    ]

    SCHEDULE_DAILY = 'daily'
    SCHEDULE_WEEKDAYS = 'weekdays'
    SCHEDULE_PER_WEEK = 'per_week'
    SCHEDULES = [
        (SCHEDULE_DAILY, 'Every day'),
        (SCHEDULE_WEEKDAYS, 'On chosen days'),
        (SCHEDULE_PER_WEEK, 'Times a week'),
    ]

    TIMES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('anytime', 'Any time'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='wellness_habits')
    name = models.CharField(max_length=80)
    kind = models.CharField(max_length=10, choices=KINDS,
                            default=KIND_YES_NO)
    # For count and duration habits: the amount that makes a day done.
    target = models.PositiveIntegerField(null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    schedule = models.CharField(max_length=10, choices=SCHEDULES,
                                default=SCHEDULE_DAILY)
    # For SCHEDULE_WEEKDAYS: the days as digits, Monday = 0 ("0246").
    weekdays = models.CharField(max_length=7, blank=True)
    # For SCHEDULE_PER_WEEK: how many times in a Monday-to-Sunday week.
    per_week = models.PositiveSmallIntegerField(null=True, blank=True)
    time_of_day = models.CharField(max_length=10, choices=TIMES,
                                   default='anytime')
    cue = models.CharField('After I...', max_length=120, blank=True)
    tiny_version = models.CharField('On a hard day, just...',
                                    max_length=120, blank=True)
    started_on = models.DateField()
    paused = models.BooleanField(default=False)
    established_at = models.DateField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wellness_habit'
        ordering = ['position', 'created_at']

    def __str__(self):
        return self.name

    @property
    def measured(self):
        return self.kind in (self.KIND_COUNT, self.KIND_DURATION)

    def weekday_set(self):
        return {int(c) for c in self.weekdays if c.isdigit()}


class HabitLog(models.Model):
    """One row per habit per day it was done (or partly done)."""
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE,
                              related_name='logs')
    date = models.DateField()
    # Count or minutes for measured habits; None for yes/no and avoid.
    value = models.PositiveIntegerField(null=True, blank=True)
    done = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wellness_habit_log'
        unique_together = [('habit', 'date')]
        ordering = ['-date']

    def __str__(self):
        return '%s on %s' % (self.habit, self.date)


class JournalEntry(models.Model):
    """WL-2, 30 Oct 2026 - one journal entry.

    THE WORDS ARE ENCRYPTED (decision 5, 30 Oct). `body` holds a Fernet
    token of the entry's JSON - {"text": ...} for a free write or a note,
    {"best", "let_go", "intention"} for the evening check-in, {"lines":
    [...]} for gratitude. Only wellness/crypto.py reads or writes it. Mood,
    energy, kind, tags and the date stay plain so the list, the filters and
    the mood line work without opening anything; tags are the person's own
    short words and say nothing a heading would not.
    """
    KINDS = [
        ('checkin', 'Evening check-in'),
        ('free', 'Free write'),
        ('gratitude', 'Gratitude'),
        ('note', 'Quick note'),
    ]
    MOODS = [(1, 'Low'), (2, 'A bit low'), (3, 'Okay'), (4, 'Good'),
             (5, 'Great')]
    ENERGY = [(1, 'Drained'), (2, 'Low'), (3, 'Steady'), (4, 'High')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='wellness_journal')
    date = models.DateField()
    kind = models.CharField(max_length=10, choices=KINDS, default='free')
    mood = models.PositiveSmallIntegerField(choices=MOODS, null=True,
                                            blank=True)
    energy = models.PositiveSmallIntegerField(choices=ENERGY, null=True,
                                              blank=True)
    tags = models.JSONField(default=list, blank=True)
    prompt = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wellness_journal_entry'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return '%s - %s' % (self.date, self.get_kind_display())


class BodyMetric(models.Model):
    """WL-2, 30 Oct 2026 - one measurement on one day. A second reading of
    the same kind on the same day replaces the first."""
    KINDS = [
        ('weight', 'Weight'),
        ('waist', 'Waist'),
        ('hips', 'Hips'),
        ('chest', 'Chest'),
        ('arm', 'Arm'),
        ('thigh', 'Thigh'),
        ('neck', 'Neck'),
        ('bodyfat', 'Body fat'),
    ]
    UNITS = {'weight': 'kg', 'bodyfat': '%'}

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='wellness_body')
    date = models.DateField()
    kind = models.CharField(max_length=10, choices=KINDS)
    value = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wellness_body_metric'
        unique_together = [('user', 'date', 'kind')]
        ordering = ['-date']

    def __str__(self):
        return '%s %s on %s' % (self.kind, self.value, self.date)

    @property
    def unit(self):
        return self.UNITS.get(self.kind, 'cm')
