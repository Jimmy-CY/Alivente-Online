# -*- coding: utf-8 -*-
"""The persistent translation stubs - THE ONLY COPY.

Translation itself is still disabled: googletrans was removed and
nothing has replaced it, so neither function calls out to anything. What
they do is serve the Greek text an editor has already TYPED, through the
English/Greek tabs on the Edit Task form.

TL-1, 4 Oct 2026 - get_translated_text declared two arguments and
project_task_list passed three, six times, every one of them behind
`if language == 'greek'`. English skipped all six and worked perfectly;
Greek raised TypeError before the template was reached and Live answered
Server Error (500). The third argument was never spare - it is the
translation stored on the model, and the signature says so now.

These were also DECLARED TWICE: here, and again inside
pages/views/projects.py with the import commented out above them. The
view imports this module now. Two copies of one definition is how a
definition drifts.

TODO: replace googletrans with deep-translator and translate on demand
when `stored` comes back blank.
"""


def ensure_project_translations(project):
    """Fill in a Project's *_greek fields. Disabled: does nothing.

    The parameter is a Project - project_task_list has always called it
    with one. It was declared as `request`, which is harmless while the
    body is `pass` and a false lead for whoever writes the body.
    """
    pass


def get_translated_text(text, stored='', language='english'):
    """The text to show for `language`.

    `stored` is the translation recorded on the model - project_name_greek
    and its three siblings, every one blank=True, so it is routinely
    empty and may arrive as None from a getattr default.

    Greek asked for and a non-blank translation on file: that. Anything
    else: the original, because a blank cell is worse than an
    untranslated one - which is the same call the template makes when it
    writes {{ item.name_greek|default:item.name }}.
    """
    if language == 'greek' and stored and stored.strip():
        return stored
    return text
