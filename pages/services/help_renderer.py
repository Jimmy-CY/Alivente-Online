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


# Canonical order of top-level menu groups. Used to sort the output of
# get_all_modules_grouped() so the Help page matches the menu layout.
_GROUP_ORDER = [
    'Property Operations',
    'Financial Management',
    'Administration',
    'Personal',
    'Notifications',
    'My Profile',
]


# When a module has NO data-module-parent, its data-module-category is
# often a legacy value ("Operational", "Administration", "Personal") that
# should be ignored for grouping. The values listed here are the
# exceptions — category values that SHOULD be treated as meaningful
# sub-section labels within their top-level group.
_EXPLICIT_SUBGROUP_CATEGORIES = {'Functional', 'System'}


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
    group = section.get('data-module-group', '')
    parent = section.get('data-module-parent', '')
    permission = section.get('data-module-permission', '')

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
        'group': group,
        'parent': parent,
        'permission': permission,
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

def get_all_modules_grouped():
    """
    Return every parsed module arranged hierarchically by top-level menu group.

    Used by the Help page (Phase 2) to build category cards and nested lists.

    Returned structure:
        [
            {
                'name': 'Property Operations',
                'direct_modules': [module_dict, ...],
                'subsections': [
                    {
                        'name': 'Reports',
                        'parent_module_slug': 'finance',
                        'parent_module_name': 'Financials',
                        'modules': [module_dict, ...],
                    },
                    ...
                ],
            },
            ...
        ]

    Rules:
        - Top-level bucket = module's data-module-group attribute.
        - Within a group:
            - Module with a data-module-parent -> goes into a sub-section named
              by its data-module-category, nested under that parent module.
            - Module with no parent but category in _EXPLICIT_SUBGROUP_CATEGORIES
              -> goes into a sub-section within the group (not nested under
              any module; parent_module_slug is None).
            - Otherwise -> direct child of the group.
        - Modules with no data-module-group are skipped entirely.
        - Groups are emitted in _GROUP_ORDER first, then any unknown groups
          alphabetically.
        - Direct modules and sub-sections are sorted alphabetically by name.
    """
    global _MODULE_CACHE

    if _MODULE_CACHE is None:
        _MODULE_CACHE = _load_all_modules()

    # Slug -> display name, for resolving parent_module_name.
    slug_to_name = {m['slug']: m['name'] for m in _MODULE_CACHE.values()}
    # Display name -> slug, so authors can write data-module-parent="Financials"
    # (readable) instead of data-module-parent="finance" (the slug).
    name_to_slug = {m['name']: m['slug'] for m in _MODULE_CACHE.values()}

    # Bucket modules by their group
    by_group = {}
    for module in _MODULE_CACHE.values():
        group = module.get('group', '')
        if not group:
            continue
        by_group.setdefault(group, []).append(module)

    # Emit groups in canonical order, then any unknown groups alphabetically
    known_groups = [g for g in _GROUP_ORDER if g in by_group]
    unknown_groups = sorted(g for g in by_group if g not in _GROUP_ORDER)

    result = []
    for group_name in known_groups + unknown_groups:
        modules = by_group[group_name]

        direct = []
        # Keyed by (parent_slug_or_None, subsection_name) -> list of modules
        subsection_buckets = {}

        for m in modules:
            raw_parent = m.get('parent', '')
            category = m.get('category', '')

            # Resolve parent to canonical slug — accept slug or display name.
            if raw_parent:
                if raw_parent in slug_to_name:
                    parent_slug = raw_parent
                elif raw_parent in name_to_slug:
                    parent_slug = name_to_slug[raw_parent]
                else:
                    # Unresolved — keep the raw value so it's visible for debugging
                    # rather than silently dropping the module into "direct".
                    parent_slug = raw_parent
            else:
                parent_slug = ''

            if parent_slug:
                key = (parent_slug, category)
                subsection_buckets.setdefault(key, []).append(m)
            elif category in _EXPLICIT_SUBGROUP_CATEGORIES:
                key = (None, category)
                subsection_buckets.setdefault(key, []).append(m)
            else:
                direct.append(m)

        direct.sort(key=lambda m: m['name'])

        subsections = []
        for (parent_slug, sub_name), mods in sorted(
            subsection_buckets.items(),
            key=lambda kv: (kv[0][0] or '', kv[0][1])
        ):
            mods.sort(key=lambda m: m['name'])
            subsections.append({
                'name': sub_name,
                'parent_module_slug': parent_slug,
                'parent_module_name': slug_to_name.get(parent_slug) if parent_slug else None,
                'modules': mods,
            })

        result.append({
            'name': group_name,
            'direct_modules': direct,
            'subsections': subsections,
        })

    return result

def clear_cache():
    """
    Force the cache to be re-read on the next call. Mostly useful
    for tests or if you build an admin action to reload without
    restarting Django.
    """
    global _MODULE_CACHE
    _MODULE_CACHE = None