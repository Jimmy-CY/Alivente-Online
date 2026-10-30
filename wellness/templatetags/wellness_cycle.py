# -*- coding: utf-8 -*-
"""wellness/templatetags/wellness_cycle.py - CY-1, 30 Oct 2026.

{% cycle_on as cy %} in wellness/base.html: the bottom bar shows Cycle only
to a person who has turned the tracker on. It opens the small settings
token of the signed-in person's own record - never anybody else's.
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def cycle_on(context):
    request = context.get('request')
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return False
    from wellness.cycle import is_on
    try:
        return is_on(user)
    except Exception:  # noqa: BLE001 - a bar must never break a page
        return False
