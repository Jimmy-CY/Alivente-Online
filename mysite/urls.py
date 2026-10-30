import os

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.http import HttpResponse

def robots_txt(request):
    content = "User-agent: *\nDisallow: /"
    return HttpResponse(content, content_type="text/plain")


def deploy_version(request):
    """What commit this process is running. DP-1, 22 Oct 2026.

    Seven characters of hex and a newline. Nothing else - not the
    branch, not the host, not the Django version, not whether DEBUG is
    on. The question this answers is 'has the thing I just pushed
    arrived', and nothing else is needed to answer it.

    WHY THIS EXISTS AT ALL. Push 4 and push 5 both landed into a
    Railway with builds paused, both printed their post-deploy checks,
    and the live site ran 3245f19 for three days. The push script now
    asks this URL until it answers the SHA that was just pushed.

    AND WHY IT IS NOT THE RAILWAY API. That would answer the same
    question and it needs a token - on a laptop, in a script, in a
    repository, a thing that can leak and must be rotated. A site
    answering a public question about itself is none of those.

    WHITELISTED, NOT ESCAPED. The value is an environment variable,
    which is somebody else string. Every character that is not a
    lowercase hex digit is dropped before anything is sent, so the
    worst a hostile value can produce is a shorter string or the word
    unknown. Nothing is interpolated, nothing is trusted.

    unknown MEANS THE BUILD DID NOT SUPPLY A SHA, not that the deploy
    failed. Railway sets RAILWAY_GIT_COMMIT_SHA on its own; a platform
    that does not can set GIT_COMMIT_SHA instead.
    """
    raw = (os.environ.get('RAILWAY_GIT_COMMIT_SHA')
           or os.environ.get('GIT_COMMIT_SHA')
           or '')
    sha = ''.join(c for c in raw.lower() if c in '0123456789abcdef')
    response = HttpResponse((sha[:7] or 'unknown') + "\n",
                            content_type="text/plain")
    # NOT CACHEABLE, by anything, ever. A cached answer to this
    # question is a wrong answer by definition - it is the one thing
    # on this site guaranteed to change on every deploy.
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    return response


def cached_media(request, path):
    """serve(), with a cache header on it. PX-1, 13 Oct 2026.

    WHY THIS IS SAFE TO CACHE FOR A YEAR. Every uploaded filename in
    this application carries a timestamp - recipe-{id}-{slug}-{stamp}.
    A re-upload produces a NEW name, so a cached copy can never be the
    wrong version of a file; it can only be a file nobody references any
    more. That is what makes `immutable` honest here rather than a
    gamble.

    WHAT IT DOES NOT FIX. serve() is Django's development file server
    and it is still what moves these bytes in production, one Python
    worker per file for the whole transfer. This header removes the
    REPEAT visits - a return to the grid costs zero requests instead of
    48 conditional ones - and does nothing at all for the first.
    Measured 13 Oct: the photos are the larger problem and PX-1 takes
    them; whether serve() still matters afterwards is a question to
    re-measure, not to guess.
    """
    response = serve(request, path, document_root=settings.MEDIA_ROOT)
    response['Cache-Control'] = 'public, max-age=31536000, immutable'
    return response

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('pages.urls')),
    path("crs/", include("crs.urls")),
    # WL-1, 30 Oct 2026 - Wellness. wellness/app/ (the installable-app
    # shell) answers without a login; everything else needs one.
    path("wellness/", include("wellness.urls")),
    path('robots.txt', robots_txt),
    # DP-1, 22 Oct 2026. Public on purpose - see deploy_version and the
    # matching line in ModuleAccessMiddleware.EXEMPT_URL_PATTERNS.
    path('version/', deploy_version, name='deploy_version'),
    re_path(r'^media/(?P<path>.*)$', cached_media),
]