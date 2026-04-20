"""
============================================================
ALIVENTE ONLINE — HELP CONTENT RENDERER SERVICE
============================================================

Reads HTML files from pages/help_content/, parses them into a
module/tabs structure, and exposes a lookup function for the
{% render_help_modal "slug" %} template tag.

How the HTML files must be structured:
---------------------------------------
Each help_content HTML file contains one or more <section>
elements, each representing one module:

    <section data-module-slug="finance_revenue_types"
             data-module-name="Revenue Types"
             data-module-icon="fa-tag"
             data-module-category="Configuration"
             data-module-subtitle="How revenue categories feed the P&amp;L">

      <article data-tab-slug="rt-overview"
               data-tab-name="Overview"
               data-tab-icon="fa-info-circle">
        <h5>...</h5>
        <p>...content HTML...</p>
      </article>

      <article data-tab-slug="rt-usage"
               data-tab-name="How to Use It"
               data-tab-icon="fa-cogs">
        ...
      </article>

    </section>

The service reads every .html file in pages/help_content/,
builds a lookup dict keyed by slug, and caches it at module
level for subsequent calls.

During development: restart Django to pick up file changes.
============================================================
"""

import os
from pathlib import Path
from bs4 import BeautifulSoup


# Where help content files live. Relative to this file's parent
# (pages/services/) going up one level to pages/, then into help_content/.
HELP_CONTENT_DIR = Path(__file__).resolve().parent.parent / 'help_content'

# Module-level cache. Populated on first call to get_help_module().
# Reset between Django process restarts.
_MODULE_CACHE = None


def _parse_module_section(section):
    """
    Convert a single <section data-module-slug="..."> element into
    a module dictionary suitable for the help_modal_shell.html template.

    Returns None if the section is missing required attributes.
    """
    slug = section.get('data-module-slug')
    if not slug:
        return None

    name = section.get('data-module-name', slug)
    icon = section.get('data-module-icon', 'fa-question-circle')
    subtitle = section.get('data-module-subtitle', '')
    category = section.get('data-module-category', 'Uncategorized')

    tabs = []
    for article in section.find_all('article', recursive=False):
        tab_slug = article.get('data-tab-slug')
        if not tab_slug:
            continue

        tab_name = article.get('data-tab-name', tab_slug)
        tab_icon = article.get('data-tab-icon', 'fa-circle')

        # decode_contents() gives us the inner HTML of the article
        # as a string, preserving all tags and formatting.
        content_html = article.decode_contents().strip()

        tabs.append({
            'slug': tab_slug,
            'name': tab_name,
            'icon': tab_icon,
            'content_html': content_html,
        })

    return {
        'slug': slug,
        'name': name,
        'icon': icon,
        'subtitle': subtitle,
        'category': category,
        'tabs': tabs,
    }


def _load_all_modules():
    """
    Scan pages/help_content/ for all .html files, parse each one,
    and return a dict {slug: module_dict}.

    Called once per Django process; result is cached in _MODULE_CACHE.
    """
    modules = {}

    if not HELP_CONTENT_DIR.exists():
        return modules

    for html_file in sorted(HELP_CONTENT_DIR.glob('*.html')):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except OSError:
            # Can't read this file — skip it rather than crashing
            continue

        soup = BeautifulSoup(content, 'html.parser')

        for section in soup.find_all('section', attrs={'data-module-slug': True}):
            module = _parse_module_section(section)
            if module:
                modules[module['slug']] = module

    return modules


def get_help_module(slug):
    """
    Return the parsed module data for a given slug, or None if
    not found. Results are cached after the first call.

    Usage (from the template tag):
        module = get_help_module("finance_revenue_types")
        if module:
            # render the modal shell with this module's data
            ...
    """
    global _MODULE_CACHE

    if _MODULE_CACHE is None:
        _MODULE_CACHE = _load_all_modules()

    return _MODULE_CACHE.get(slug)


def get_all_modules():
    """
    Return every parsed module as a list, sorted by category then name.
    Intended for the future Help Section page (Step 4) which will list
    all help topics for browsing and searching.
    """
    global _MODULE_CACHE

    if _MODULE_CACHE is None:
        _MODULE_CACHE = _load_all_modules()

    return sorted(
        _MODULE_CACHE.values(),
        key=lambda m: (m['category'], m['name'])
    )


def clear_cache():
    """
    Force the cache to be re-read on the next call. Mostly useful
    for tests or if you build an admin action to reload without
    restarting Django.
    """
    global _MODULE_CACHE
    _MODULE_CACHE = None