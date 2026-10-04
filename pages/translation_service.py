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

TR-2, 4 Oct 2026 - the TODO above said "replace googletrans with
deep-translator". TR-1 did that and it could not reach Google from
Railway. translate_to_greek below uses the Anthropic Messages API
instead - the same endpoint, key and urllib call that
pages/services/invoice_verification.py has been making in production,
and unlike the scraper it can be given a timeout and told what it is
reading. Demetri: "Can we not use our AI API for translation?"
"""
import json
import os
import urllib.error
import urllib.request

# The same endpoint and default model invoice_verification uses. A task
# name is a handful of words, so haiku is the right weight; both are
# overridable by environment variable for the same reason that one is.
API_URL = 'https://api.anthropic.com/v1/messages'
DEFAULT_MODEL = 'claude-haiku-4-5'
DEFAULT_TIMEOUT = 20.0

# WHY THE PROMPT SAYS WHAT THE TEXT IS. A generic engine reads
# "Backsplash" as a splash of water and "Snagging" as catching on a nail.
# Naming the domain in one sentence is the whole difference between a
# translation a Greek builder would use and one he would laugh at.
#
# RETURN ONLY THE TRANSLATION is load-bearing. Anything conversational
# would be written straight into the Greek field as if it were the
# answer - the failure TR-1 existed to stop, arriving by a new route.
_PROMPT = """You are translating short text from English into Greek for a
property management and maintenance system used in Cyprus.

The text is a task name or a task description from a renovation or
maintenance project - things like Backsplash, Snagging, Granite Top
Replacement, Update Kitchen, Replace Unit. Translate them the way a Greek
builder or property manager would say them, not word by word.

Keep proper nouns, property names, people's names and numbers exactly as
they are. Keep the same capitalisation style. Do not add anything.

Return ONLY the Greek translation, with no quotes, no explanation and no
alternatives."""

# Long enough for a description, short enough that a runaway answer
# cannot be mistaken for a task name.
MAX_TOKENS = 1000

# Anything longer than this is not a task name and is not what this was
# built for; refusing is cheaper than a surprise bill.
MAX_CHARS = 4000


def _config():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    model = os.environ.get('TRANSLATE_MODEL', DEFAULT_MODEL)
    try:
        timeout = float(os.environ.get('TRANSLATE_TIMEOUT', DEFAULT_TIMEOUT))
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT
    return api_key, model, timeout


def translate_to_greek(text):
    """English to Greek. Returns (ok, text, reason).

    THE CONTRACT IS TR-1'S AND IT DOES NOT MOVE. On failure the second
    element is None - never the input. Returning the English from here
    is what made a failed translation arrive as a green tick with the
    English sitting in the Greek box, and the engine changing underneath
    is not a reason to let that back in.
    """
    text = (text or '').strip()
    if not text:
        return (False, None, 'There is nothing to translate.')
    if len(text) > MAX_CHARS:
        return (False, None,
                'That text is too long to translate (%d characters).'
                % len(text))

    api_key, model, timeout = _config()
    if not api_key:
        return (False, None, 'Translation is not configured on this server.')

    body = json.dumps({
        'model': model,
        'max_tokens': MAX_TOKENS,
        'system': _PROMPT,
        'messages': [{'role': 'user', 'content': text}],
    }).encode('utf-8')

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        print('Translation API returned HTTP %s' % exc.code)
        return (False, None,
                'The translation service refused the request (HTTP %s).'
                % exc.code)
    except Exception as exc:                                # noqa: BLE001
        print('Translation call failed: %s' % exc)
        return (False, None, 'The translation service could not be reached.')

    blocks = data.get('content') or []
    out = ''.join(b.get('text', '') for b in blocks
                  if b.get('type') == 'text').strip()
    if not out:
        return (False, None, 'The translation service returned nothing.')
    return (True, out, '')


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
