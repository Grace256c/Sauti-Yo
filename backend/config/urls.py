"""
URL configuration for the Sauti Yo project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView


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

    path(
        "api/channels/",
        include("apps.channels.urls"),
    ),
    path(
    "api/chat/",
    include("apps.chat.urls"),
),
]


# Serve frontend pages through Django in production.
# API, admin, static and media URLs are excluded.
if not settings.DEBUG:
    urlpatterns += [
        re_path(
            r"^(?!(?:api|admin|static|media)(?:/|$)).*$",
            TemplateView.as_view(template_name="index.html"),
            name="react-app",
        ),
    ]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
