# -*- coding: utf-8 -*-
"""wellness/templatetags/wellness_modules.py - WL-9, 31 Oct 2026.

{% modules_on as mods %} in wellness/base.html: the bottom bar shows only
the sections this person has switched on (Settings, Your sections). The
signed-in person's own choices, never anybody else's.
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def modules_on(context):
    request = context.get('request')
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return set()
    cached = getattr(request, '_wellness_modules', None)
    if cached is not None:
        return cached
    from wellness.modules import on_set
    try:
        got = on_set(user)
    except Exception:  # noqa: BLE001 - a bar must never break a page
        from wellness.modules import SWITCHED
        got = set(SWITCHED)
    request._wellness_modules = got
    return got


@register.simple_tag(takes_context=True)
def fx_state(context):
    """WL-15, 2 Nov 2026 - 'on' or 'off': sounds and vibration for a tick,
    a badge and a save (Settings > Sounds and vibration; on by default -
    Demetri, 19:39)."""
    request = context.get('request')
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return 'on'
    try:
        from wellness.models import WellnessProfile
        p = WellnessProfile.objects.filter(user=user).first()
        return 'off' if p and (p.prefs or {}).get('sounds_off') else 'on'
    except Exception:  # noqa: BLE001 - a sound must never break a page
        return 'on'
