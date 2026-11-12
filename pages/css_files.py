# -*- coding: utf-8 -*-
"""SP-1, 12 Nov 2026 - base.html's stylesheets, served as cached files.

base.html carried about 197 KB of CSS written into the page, so every
signed-in page sent it again (about 59 KB after Cloudflare compression).

The CSS stays in base.html, word for word - it is still the one place to
read and edit it, and every suite that reads base.html still reads it.
What changes is what the browser receives: each block wrapped in
{% cached_css %} ... {% endcached_css %} becomes

    <link rel="stylesheet" href="/alv-css/<hash>.css">

The hash is of the CSS itself, so any edit gives a new address and the
file can be cached for a year without ever going stale.

Any worker can answer for any hash: if it has not seen the hash yet it
compiles the templates in CSS_TEMPLATES, which registers their blocks.

settings.ALV_CSS_FILES = False puts the CSS back inline, as before.
"""
import hashlib
import re

from django.http import Http404, HttpResponse
from django.template.loader import get_template

SHEETS = {}
CSS_TEMPLATES = ('base.html',)

_STYLE = re.compile(r'\A\s*<style[^>]*>(.*)</style>\s*\Z', re.S)


def register(raw):
    """Strip the <style> wrapper, store the CSS, return (digest, css)."""
    m = _STYLE.match(raw)
    css = m.group(1) if m else raw
    digest = hashlib.sha256(css.encode('utf-8')).hexdigest()[:16]
    SHEETS[digest] = css
    return digest, css


def warm():
    """Compile the templates that carry cached blocks, registering them."""
    from pages.templatetags.alv_assets import CachedCssNode
    for name in CSS_TEMPLATES:
        tpl = get_template(name).template
        for node in tpl.nodelist.get_nodes_by_type(CachedCssNode):
            node.prepare()


def stylesheet(request, digest):
    if digest not in SHEETS:
        warm()
    css = SHEETS.get(digest)
    if css is None:
        raise Http404('No such stylesheet')
    resp = HttpResponse(css, content_type='text/css; charset=utf-8')
    resp['Cache-Control'] = 'public, max-age=31536000, immutable'
    return resp
