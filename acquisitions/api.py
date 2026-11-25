"""
api.py - RA25, 25 Nov 2026. The door Claude's search tasks use.

    GET  api/scenarios/              the active scenarios, their rules and
                                     what each already tracks (?only=3,7)
    POST api/runs/                   start a run for one scenario
    POST api/runs/<id>/report/       listings, site results, and the summary
                                     with "finished": true

No login: a shared key, ACQ_INTAKE_KEY, that Demetri sets on Railway and
in the search task's environment - never in chat, never in a file, never
in the activity log. It is sent in the X-Acq-Key header. Without the
setting every call answers 503, so nothing can be written until he sets it;
a key shorter than 32 characters counts as not set. The key is never
echoed back, and a wrong one is answered without saying why.

Everything else is in intake.py.
"""
import hmac
import json
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import intake
from .models import SearchRun

KEY_ENV = "ACQ_INTAKE_KEY"
HEADER = "X-Acq-Key"
MIN_KEY = 32
MAX_BODY = 2 * 1024 * 1024


def configured():
    return len((os.environ.get(KEY_ENV) or "").strip()) >= MIN_KEY


def _refuse(error, status):
    return JsonResponse({"ok": False, "error": error}, status=status)


def _door(request, method):
    """None when the request may come in; otherwise the answer to give."""
    if request.method != method:
        return _refuse("use %s" % method, 405)
    if not configured():
        return _refuse("not configured", 503)
    key = (os.environ.get(KEY_ENV) or "").strip().encode()
    given = (request.headers.get(HEADER) or "").strip().encode()
    if not hmac.compare_digest(key, given):
        return _refuse("key", 401)
    return None


def _body(request):
    raw = request.read(MAX_BODY + 1)
    if len(raw) > MAX_BODY:
        raise intake.Refused("too big: send the listings in several reports")
    try:
        return json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, ValueError):
        raise intake.Refused("not JSON")


@csrf_exempt
def scenarios(request):
    shut = _door(request, "GET")
    if shut:
        return shut
    only = [int(x) for x in (request.GET.get("only") or "").split(",") if x.strip().isdigit()]
    return JsonResponse(dict(intake.scenarios_out(only), ok=True))


@csrf_exempt
def run_start(request):
    shut = _door(request, "POST")
    if shut:
        return shut
    try:
        run = intake.start_run(_body(request))
    except intake.Refused as e:
        return _refuse(str(e), 400)
    return JsonResponse({"ok": True, "run_id": run.pk, "scenario": run.scenario.name},
                        status=201)


@csrf_exempt
def run_report(request, pk):
    shut = _door(request, "POST")
    if shut:
        return shut
    run = SearchRun.objects.select_related("scenario").filter(pk=pk).first()
    if run is None:
        return _refuse("no such run", 404)
    try:
        got = intake.report(run, _body(request))
    except intake.Refused as e:
        return _refuse(str(e), 400)
    return JsonResponse(dict(got, ok=True))
