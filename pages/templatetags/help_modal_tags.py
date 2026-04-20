"""
============================================================
ALIVENTE ONLINE — HELP MODAL TEMPLATE TAG
============================================================

Registers the {% render_help_modal "slug" %} template tag.

Usage in a template:
    {% load help_modal_tags %}
    ...
    <button type="button" class="btn btn-info"
            data-toggle="modal"
            data-target="#finance_revenue_typesHelpModal">
      <i class="fas fa-question-circle"></i> Help
    </button>
    {% render_help_modal "finance_revenue_types" %}

The tag:
  1. Looks up the module in pages/help_content/ via help_renderer
  2. Renders pages/templates/help_modal_shell.html with the module data
  3. Returns an empty string if the slug doesn't exist (safe fallback)
============================================================
"""

from django import template
from pages.services.help_renderer import get_help_module


register = template.Library()


@register.inclusion_tag('help_modal_shell.html')
def render_help_modal(slug):
    """
    Render the help modal shell template with the module whose
    slug matches the argument.

    If the slug is not found in any of the help_content files,
    returns an empty context so the shell template renders nothing
    useful (and crucially, doesn't crash the page).

    Args:
        slug: The module slug, e.g. "finance_revenue_types"

    Returns:
        A context dict for help_modal_shell.html. If the module
        is found, it will contain `module` and `found=True`. If
        not, it will contain `found=False` and no `module` key.
    """
    module = get_help_module(slug)

    if module is None:
        # Gracefully handle unknown slugs — the shell template
        # checks for `found` and renders nothing if missing.
        return {
            'found': False,
            'requested_slug': slug,
        }

    return {
        'found': True,
        'module': module,
    }