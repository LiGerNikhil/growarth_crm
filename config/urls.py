"""
URL configuration for CRM project.
"""

from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
import os

def robots_txt(request):
    """Serve robots.txt file"""
    robots_path = os.path.join(settings.BASE_DIR, 'robots.txt')
    if os.path.exists(robots_path):
        with open(robots_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/plain')
    else:
        return HttpResponse("User-agent: *\nDisallow: /", content_type='text/plain')

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # robots.txt
    path("robots.txt", robots_txt),

    # Authentication URLs
    path("accounts/", include("apps.accounts.urls")),

    # Core URLs
    path("", include("apps.core.urls")),

    # CRM URLs
    path("", include("apps.crm.urls")),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Custom error handlers
handler404 = "apps.core.views.page_not_found"
handler500 = "apps.core.views.server_error"
