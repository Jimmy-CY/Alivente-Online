# -*- coding: utf-8 -*-
"""wellness/templatetags/wellness_help.py - WL-6, 31 Oct 2026.

{% screen_help as h %} in wellness/base.html: the help for the screen being
shown (by its URL name) and the general questions, for the sheet the ?
opens.
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def screen_help(context):
    from wellness import guide, help as HELP
    request = context.get('request')
    match = getattr(request, 'resolver_match', None)
    name = getattr(match, 'url_name', '') or ''
    return {'screen': HELP.for_url_name(name), 'general': guide.HOWTO,
            'name': name}
