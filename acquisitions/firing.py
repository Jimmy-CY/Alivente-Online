"""
firing.py - RA24, 25 Nov 2026. Starting Claude's search from the app.

Demetri, 25 Nov, on the Run search now pop-up that only said how to start
a search in the Claude app: "Can we not trigger the run now from the app,
or some kind of job?" Yes: Claude's scheduled search task can be given an
API trigger (claude.ai/code/routines -> the task -> Edit -> Trigger + ->
API). That gives a Fire URL and a token, which Demetri keeps on Railway as
ROUTINE_FIRE_URL and ROUTINE_FIRE_TOKEN - never in chat, never in a file,
never in the activity log. POSTing to the URL starts a run; the text sent
with it names the scenarios to search, and the task's own prompt says to
search only those.

Without the two settings, configured() is False and every Run button shows
how to start a search in the Claude app instead, as before.
"""
import json
import logging
import os
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

URL_ENV = "ROUTINE_FIRE_URL"
TOKEN_ENV = "ROUTINE_FIRE_TOKEN"
# Only Anthropic's own endpoint: a mistyped or planted URL is never sent the token.
URL_START = "https://api.anthropic.com/v1/claude_code/routines/"
BETA = "experimental-cc-routine-2026-04-01"
TIMEOUT = 20


def _url():
    return (os.environ.get(URL_ENV) or "").strip()


def configured():
    """Both settings are there, and the URL is Anthropic's fire endpoint."""
    url = _url()
    return bool(url.startswith(URL_START) and url.endswith("/fire")
                and (os.environ.get(TOKEN_ENV) or "").strip())


def payload(scenarios):
    """The text the run is started with: the scenarios to search, by name
    (the task's prompt searches only the ones named)."""
    names = "; ".join('"%s"' % s.name for s in scenarios)
    return ("Alivente Online asks for a search now of %d scenario%s: %s. "
            "Search only these, then report to the app as usual."
            % (len(scenarios), "" if len(scenarios) == 1 else "s", names))


def fire(scenarios, opener=None):
    """Start one run for these scenarios. Returns (ok, words, session_url).
    The words are for the person; the token is never in them, nor logged."""
    if not configured():
        return False, "Starting a search from the app is not set up yet.", ""
    if not scenarios:
        return False, "Tick at least one scenario.", ""
    body = json.dumps({"text": payload(scenarios)}).encode("utf-8")
    req = urllib.request.Request(_url(), data=body, method="POST", headers={
        "Authorization": "Bearer %s" % os.environ.get(TOKEN_ENV, "").strip(),
        "anthropic-beta": BETA,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    })
    try:
        with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        log.warning("Search start refused: HTTP %s", e.code)
        if e.code in (401, 403):
            return False, ("Claude refused the start: the token on Railway is wrong or was "
                           "regenerated. Generate a new one and update ROUTINE_FIRE_TOKEN."), ""
        if e.code == 429:
            return False, "Too many starts this hour - try again later.", ""
        return False, "Claude could not start the search just now (error %s)." % e.code, ""
    except Exception as e:                                  # noqa: BLE001
        log.warning("Search start failed: %s", type(e).__name__)
        return False, "Claude could not be reached just now. Try again in a minute.", ""
    url = str(data.get("claude_code_session_url") or "")
    if not url.startswith("https://claude.ai/"):
        url = ""
    return True, "Search started for %s." % ", ".join(s.name for s in scenarios), url
