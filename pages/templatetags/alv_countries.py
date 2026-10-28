# -*- coding: utf-8 -*-
"""alv_countries - PC-1, 28 Oct 2026.

    {% load alv_countries %}
    <select name="tenant_id_country">{% id_country_options tresults.tenant_id_country %}</select>

The <option>s for a Passport/ID country: a blank "Country" first, then
Cyprus and Greece, then the rest of pages/countries.py A to Z, with the
saved value selected. A saved value that is not on the list - typed
before the list existed - is offered at the top, selected, rather than
silently replaced by the blank on the next save.
"""
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from pages.countries import ID_COUNTRIES, ID_COUNTRIES_TOP

register = template.Library()


@register.simple_tag
def id_country_options(chosen=''):
    chosen = (chosen or '').strip()
    out = ['<option value="">Country</option>']
    if chosen and chosen not in ID_COUNTRIES:
        out.append('<option value="%s" selected>%s</option>'
                   % (escape(chosen), escape(chosen)))
    for i, name in enumerate(ID_COUNTRIES):
        if i == len(ID_COUNTRIES_TOP):
            out.append('<option disabled>&#8212;&#8212;&#8212;&#8212;</option>')
        out.append('<option value="%s"%s>%s</option>'
                   % (escape(name), ' selected' if name == chosen else '',
                      escape(name)))
    return mark_safe(''.join(out))
