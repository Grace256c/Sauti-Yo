from django.urls import path

from .views import (
    PartnerOrganisationCreateAPIView,
    PartnerOrganisationDetailAPIView,
    PartnerServiceConfigurationAPIView,
    PartnerVerificationRequestAPIView,
    PartnerVerificationDocumentAPIView,
    PartnerVerificationDocumentDetailAPIView,
)


urlpatterns = [
    path(
        "create/",
        PartnerOrganisationCreateAPIView.as_view(),
        name="partner-organisation-create",
    ),

    path(
        "<int:pk>/",
        PartnerOrganisationDetailAPIView.as_view(),
        name="partner-organisation-detail",
    ),

    path(
        "<int:organisation_id>/services/",
        PartnerServiceConfigurationAPIView.as_view(),
        name="partner-service-configuration",
    ),

    path(
        "<int:organisation_id>/verification/",
        PartnerVerificationRequestAPIView.as_view(),
        name="partner-verification-request",
    ),
    path(
        "<int:organisation_id>/verification/documents/",
        PartnerVerificationDocumentAPIView.as_view(),
        name="partner-verification-document-upload",
    ),

    path(
        "<int:organisation_id>/verification/documents/<int:document_id>/",
        PartnerVerificationDocumentDetailAPIView.as_view(),
        name="partner-verification-document-detail",
    ),
]



from .views import PartnerPreferencesAPIView


urlpatterns += [
    path(
        "<int:organisation_id>/preferences/",
        PartnerPreferencesAPIView.as_view(),
        name="partner-preferences",
    ),
]



from .views import PublicPartnerMatchAPIView


urlpatterns += [
    path(
        "matches/",
        PublicPartnerMatchAPIView.as_view(),
        name="partner-public-matches",
    ),
]
