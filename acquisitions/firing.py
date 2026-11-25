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

RA27, 25 Nov 2026 - THE PC SEARCH. Its task belongs to Demetri's Claude
project and to his computer, and such a task offers no API trigger today
(its Edit shows Schedule only). So Start the PC search opens that task's
own page in Claude (PC_TASK_URL, or ACQ_PC_TASK_URL on Railway), where he
presses Run now, and the app follows the run as it reports. Should Claude
ever offer the trigger there, PC_FIRE_URL and PC_FIRE_TOKEN on Railway make
the same button start it directly - fire(..., which="pc").
"""
import json
import logging
import os
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

URL_ENV = "ROUTINE_FIRE_URL"
TOKEN_ENV = "ROUTINE_FIRE_TOKEN"
# RA27 - the PC search's own pair, and the page of its task in Claude.
ENVS = {"cloud": (URL_ENV, TOKEN_ENV), "pc": ("PC_FIRE_URL", "PC_FIRE_TOKEN")}
PC_TASK_ENV = "ACQ_PC_TASK_URL"
PC_TASK_URL = "https://claude.ai/code/routines/trig_0177axGHkU4JSNT6suGb7X16"
# Only Anthropic's own endpoint: a mistyped or planted URL is never sent the token.
URL_START = "https://api.anthropic.com/v1/claude_code/routines/"
BETA = "experimental-cc-routine-2026-04-01"
TIMEOUT = 20


def _url(which="cloud"):
    return (os.environ.get(ENVS[which][0]) or "").strip()


def _token(which="cloud"):
    return (os.environ.get(ENVS[which][1]) or "").strip()


def configured(which="cloud"):
    """Both settings are there, and the URL is Anthropic's fire endpoint."""
    url = _url(which)
    return bool(url.startswith(URL_START) and url.endswith("/fire") and _token(which))


def pc_task_url():
    """RA27 - where Start the PC search sends him: the task's page in Claude."""
    url = (os.environ.get(PC_TASK_ENV) or "").strip()
    return url if url.startswith("https://claude.ai/") else PC_TASK_URL


def payload(scenarios):
    """The text the run is started with: the scenarios to search, by name
    (the task's prompt searches only the ones named)."""
    names = "; ".join('"%s"' % s.name for s in scenarios)
    # RA25 - and by id, for the app's api/scenarios/?only= (intake.py).
    ids = ",".join(str(s.pk) for s in scenarios if getattr(s, "pk", None))
    return ("Alivente Online asks for a search now of %d scenario%s: %s%s. "
            "Search only these, then report to the app as usual."
            % (len(scenarios), "" if len(scenarios) == 1 else "s", names,
               " (scenario ids %s)" % ids if ids else ""))


def fire(scenarios, opener=None, which="cloud"):
    """Start one run for these scenarios. Returns (ok, words, session_url).
    The words are for the person; the token is never in them, nor logged."""
    if not configured(which):
        return False, "Starting a search from the app is not set up yet.", ""
    if not scenarios:
        return False, "Tick at least one scenario.", ""
    body = json.dumps({"text": payload(scenarios)}).encode("utf-8")
    req = urllib.request.Request(_url(which), data=body, method="POST", headers={
        "Authorization": "Bearer %s" % _token(which),
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
                           "regenerated. Generate a new one and update %s." % ENVS[which][1]), ""
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
