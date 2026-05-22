from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.http import HttpResponse

def robots_txt(request):
    content = "User-agent: *\nDisallow: /"
    return HttpResponse(content, content_type="text/plain")

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('pages.urls')),
    path("crs/", include("crs.urls")),
    path('robots.txt', robots_txt),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]