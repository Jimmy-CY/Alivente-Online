from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.http import HttpResponse

def robots_txt(request):
    content = "User-agent: *\nDisallow: /"
    return HttpResponse(content, content_type="text/plain")


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
    path('robots.txt', robots_txt),
    re_path(r'^media/(?P<path>.*)$', cached_media),
]