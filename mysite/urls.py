# mysite/urls.py - Add production media serving

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('pages.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ALSO serve media files in Railway production
# Railway doesn't have nginx configured to serve media files
if os.environ.get('RAILWAY_ENVIRONMENT_NAME') or os.environ.get('RAILWAY_PROJECT_ID'):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Alternative: Serve media files in both development AND production
# (uncomment this line and comment out the above if you prefer)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)