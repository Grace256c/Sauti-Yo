"""
URL configuration for the Sauti Yo project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "api/auth/",
        include("apps.core.urls"),
    ),
    path(
        "api/rights/",
        include("apps.rights.urls"),
    ),
    path(
        "api/support/",
        include("apps.support.urls"),
    ),
    path(
        "api/content/",
        include("apps.content.urls"),
    ),
    path(
        "api/partners/",
        include("apps.partners.urls"),
    ),
    path(
        "api/referrals/",
        include("apps.referrals.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
