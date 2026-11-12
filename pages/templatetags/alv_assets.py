# -*- coding: utf-8 -*-
"""SP-1, 12 Nov 2026 - {% cached_css %} ... {% endcached_css %}.

Wraps one <style> block that holds no template tags. The page receives a
<link> to a cached file instead of the CSS itself. See pages/css_files.py.
"""
from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.html import escape

from pages import css_files

register = template.Library()


class CachedCssNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist
        self.digest = None
        self.css = None

    def prepare(self):
        if self.digest is None:
            raw = self.nodelist.render(template.Context())
            self.digest, self.css = css_files.register(raw)
        elif self.digest not in css_files.SHEETS:
            css_files.SHEETS[self.digest] = self.css
        return self.digest

    def render(self, context):
        digest = self.prepare()
        if not getattr(settings, 'ALV_CSS_FILES', True):
            return '<style>%s</style>' % self.css
        return '<link rel="stylesheet" href="%s">' % escape(
            reverse('alv_css', args=[digest]))


@register.tag
def cached_css(parser, token):
    nodelist = parser.parse(('endcached_css',))
    parser.delete_first_token()
    return CachedCssNode(nodelist)
