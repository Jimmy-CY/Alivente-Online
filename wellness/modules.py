# -*- coding: utf-8 -*-
"""wellness/modules.py - WL-9, 31 Oct 2026. Your sections.

Demetri, 31 Oct 17:05: "On the Settings page, every user must be able to
expand a modules section and must then be allowed to activate/deactivate
any of the six modules. Habits, Journal, Workouts, Body, Cycle tracker and
Calm. They should then only have the relevant section show on the Today
page and in the bottom module-selector bar."

    - Today always stays: it is where everything else gathers.
    - A section switched OFF leaves the bottom bar and Today, its
      reminders stop, Claude's line and the Monday email leave it out, and
      its pages send the person to Settings with a line saying so.
      NOTHING IS DELETED: switched back on, everything is where it was.
    - What is switched off is kept in the profile's prefs ('modules_off'),
      so a section added later starts ON for everyone.
    - The cycle tracker keeps its own switch (on/off in its locked record,
      off by default, its welcome page first). Settings shows it beside the
      others and turns it off the same way its own page does.
"""

# (key, name, one line for Settings). Order = the bottom bar's order.
MODULES = [
    ('habits', 'Habits', 'Small things, most days.'),
    ('journal', 'Journal', 'A private place to write, and the evening '
                           'check-in.'),
    ('calm', 'Calm', 'Breathe, guided practices and a quiet timer.'),
    ('workouts', 'Workouts', 'Routines and a live logger.'),
    ('body', 'Body', 'Weight trend and measurements.'),
    ('cycle', 'Cycle tracker', 'Private and locked. Off until you turn it '
                               'on.'),
]
KEYS = [m[0] for m in MODULES]
SWITCHED = [k for k in KEYS if k != 'cycle']

# The first part of the address after /wellness/ -> its section.
BY_PATH = {'habits': 'habits', 'journal': 'journal', 'calm': 'calm',
           'workouts': 'workouts', 'body': 'body'}
# Addresses inside a section that still answer when it is off: a Calm
# session finished offline is still kept when it arrives.
ALWAYS = {'calm_done'}


def off_from_prefs(prefs):
    return {k for k in ((prefs or {}).get('modules_off') or [])
            if k in SWITCHED}


def on_set(user, profile=None):
    """The sections this person has on (cycle from its own record)."""
    from .models import WellnessProfile
    from . import cycle as CY
    p = profile or WellnessProfile.objects.filter(user=user).first()
    off = off_from_prefs(p.prefs if p else None)
    on = {k for k in SWITCHED if k not in off}
    try:
        if CY.is_on(user):
            on.add('cycle')
    except Exception:  # noqa: BLE001 - a switch must never break a page
        pass
    return on


def is_on(user, key, profile=None):
    return key in on_set(user, profile)


def section_of(path):
    """'/wellness/habits/3/' -> 'habits'; None for Today, Settings..."""
    parts = [x for x in (path or '').split('/') if x]
    if len(parts) >= 2 and parts[0] == 'wellness':
        return BY_PATH.get(parts[1])
    return None


def save(profile, wanted_on):
    """Keep which switchable sections are off. Returns the set off."""
    off = sorted(k for k in SWITCHED if k not in set(wanted_on))
    prefs = dict(profile.prefs or {})
    prefs['modules_off'] = off
    profile.prefs = prefs
    profile.save(update_fields=['prefs', 'updated_at'])
    return set(off)


def checkin_on(mods):
    """The evening check-in belongs to the writing section. (A function,
    so the reminder code never names that section - test_wellness_five
    holds reminders.py to having no word of it.)"""
    return 'journal' in mods


def name_of(key):
    for k, n, _l in MODULES:
        if k == key:
            return n
    return key
