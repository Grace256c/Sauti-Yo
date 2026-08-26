from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.support.models import SupportService

from .models import (
    PartnerMember,
    PartnerOrganisation,
    PartnerServiceConfiguration,
    PartnerVerificationRequest,
    PartnerVerificationDocument,
)
from .permissions import (
    CanManagePartnerOrganisation,
    IsPartnerOrganisationMember,
)
from .serializers import (
    PartnerOrganisationSerializer,
    PartnerServiceConfigurationSerializer,
    PartnerVerificationRequestSerializer,
    PartnerVerificationDocumentSerializer,
)


def get_user_partner_organisation(
    user,
    organisation_id,
):
    """
    Return an active partner organisation only when the
    authenticated user has an active membership in it.
    """

    return get_object_or_404(
        PartnerOrganisation.objects.select_related(
            "support_service"
        ),
        pk=organisation_id,
        is_active=True,
        members__user=user,
        members__is_active=True,
    )


class PartnerOrganisationDetailAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsPartnerOrganisationMember,
    ]

    def get(
        self,
        request,
        pk,
    ):
        organisation = get_object_or_404(
            PartnerOrganisation.objects
            .select_related(
                "support_service"
            )
            .prefetch_related(
                "members",
                "members__user",
                "verification_requests",
                "verification_requests__documents",
                "verification_requests__submitted_by",
                "verification_requests__reviewed_by",
            ),
            pk=pk,
            is_active=True,
            members__user=request.user,
            members__is_active=True,
        )

        self.check_object_permissions(
            request,
            organisation,
        )

        serializer = PartnerOrganisationSerializer(
            organisation,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(
        self,
        request,
        pk,
    ):
        organisation = get_object_or_404(
            PartnerOrganisation.objects.select_related(
                "support_service"
            ),
            pk=pk,
            is_active=True,
            members__user=request.user,
            members__is_active=True,
        )

        self.check_object_permissions(
            request,
            organisation,
        )

        support_service_data = request.data.get(
            "support_service",
            {},
        )

        if (
            support_service_data is not None
            and not isinstance(
                support_service_data,
                dict,
            )
        ):
            return Response(
                {
                    "support_service": (
                        "Support service data must be "
                        "an object."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        support_service = (
            organisation.support_service
        )

        support_service_fields = [
            "name",
            "service_type",
            "description",
            "phone_number",
            "alternate_phone_number",
            "email",
            "website",
            "availability",
            "coverage",
        ]

        for field in support_service_fields:
            if field in support_service_data:
                setattr(
                    support_service,
                    field,
                    support_service_data[field],
                )

        support_service.save()

        organisation_data = {
            key: value
            for key, value
            in request.data.items()
            if key != "support_service"
        }

        serializer = PartnerOrganisationSerializer(
            organisation,
            data=organisation_data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        organisation = (
            PartnerOrganisation.objects
            .select_related(
                "support_service"
            )
            .prefetch_related(
                "members",
                "members__user",
                "verification_requests",
                "verification_requests__documents",
                "verification_requests__submitted_by",
                "verification_requests__reviewed_by",
            )
            .get(
                pk=organisation.pk
            )
        )

        response_serializer = (
            PartnerOrganisationSerializer(
                organisation,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class PartnerOrganisationCreateAPIView(APIView):
    """
    Temporary authenticated organisation creation endpoint.

    Later, public onboarding/registration can be separated
    from authenticated partner workspace access.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    @transaction.atomic
    def post(
        self,
        request,
    ):
        support_service_data = request.data.get(
            "support_service",
            {},
        )

        if not isinstance(
            support_service_data,
            dict,
        ):
            return Response(
                {
                    "support_service": (
                        "Support service data must be "
                        "an object."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = support_service_data.get(
            "name"
        )

        if not name:
            return Response(
                {
                    "support_service": {
                        "name": (
                            "Organisation name is required."
                        )
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        support_service = (
            SupportService.objects.create(
                name=name,
                service_type=support_service_data.get(
                    "service_type",
                    "",
                ),
                description=support_service_data.get(
                    "description",
                    "",
                ),
                phone_number=support_service_data.get(
                    "phone_number",
                    "",
                ),
                alternate_phone_number=support_service_data.get(
                    "alternate_phone_number",
                    "",
                ),
                email=support_service_data.get(
                    "email",
                    "",
                ),
                website=support_service_data.get(
                    "website",
                    "",
                ),
                availability=support_service_data.get(
                    "availability",
                    "",
                ),
                coverage=support_service_data.get(
                    "coverage",
                    "",
                ),
                verification_status=(
                    "review_required"
                ),
                is_active=True,
            )
        )

        organisation = (
            PartnerOrganisation.objects.create(
                support_service=(
                    support_service
                ),
                organisation_type=(
                    request.data.get(
                        "organisation_type",
                        "",
                    )
                ),
                registration_number=(
                    request.data.get(
                        "registration_number",
                        "",
                    )
                ),
                year_established=(
                    request.data.get(
                        "year_established"
                    )
                ),
                headquarters_district=(
                    request.data.get(
                        "headquarters_district",
                        "",
                    )
                ),
                physical_address=(
                    request.data.get(
                        "physical_address",
                        "",
                    )
                ),
                public_email=(
                    request.data.get(
                        "public_email",
                        "",
                    )
                ),
                public_phone=(
                    request.data.get(
                        "public_phone",
                        "",
                    )
                ),
            )
        )

        PartnerServiceConfiguration.objects.create(
            organisation=organisation,
        )

        PartnerMember.objects.create(
            organisation=organisation,
            user=request.user,
            role="owner",
            is_active=True,
        )

        serializer = PartnerOrganisationSerializer(
            organisation,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class PartnerServiceConfigurationAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
        CanManagePartnerOrganisation,
    ]

    def get(
        self,
        request,
        organisation_id,
    ):
        organisation = (
            get_user_partner_organisation(
                request.user,
                organisation_id,
            )
        )

        self.check_object_permissions(
            request,
            organisation,
        )

        configuration = get_object_or_404(
            PartnerServiceConfiguration,
            organisation=organisation,
        )

        serializer = (
            PartnerServiceConfigurationSerializer(
                configuration
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(
        self,
        request,
        organisation_id,
    ):
        organisation = (
            get_user_partner_organisation(
                request.user,
                organisation_id,
            )
        )

        self.check_object_permissions(
            request,
            organisation,
        )

        configuration = get_object_or_404(
            PartnerServiceConfiguration,
            organisation=organisation,
        )

        serializer = (
            PartnerServiceConfigurationSerializer(
                configuration,
                data=request.data,
                partial=True,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class PartnerVerificationRequestAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
        CanManagePartnerOrganisation,
    ]

    def get(
        self,
        request,
        organisation_id,
    ):
        organisation = (
            get_user_partner_organisation(
                request.user,
                organisation_id,
            )
        )

        self.check_object_permissions(
            request,
            organisation,
        )

        verification = (
            PartnerVerificationRequest.objects
            .filter(
                organisation=organisation
            )
            .prefetch_related(
                "documents"
            )
            .select_related(
                "submitted_by",
                "reviewed_by",
            )
            .first()
        )

        if verification is None:
            return Response(
                None,
                status=status.HTTP_200_OK,
            )

        serializer = (
            PartnerVerificationRequestSerializer(
                verification,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def post(
        self,
        request,
        organisation_id,
    ):
        organisation = (
            get_user_partner_organisation(
                request.user,
                organisation_id,
            )
        )

        self.check_object_permissions(
            request,
            organisation,
        )

        latest = (
            PartnerVerificationRequest.objects
            .filter(
                organisation=organisation
            )
            .first()
        )

        if (
            latest
            and latest.status
            in {
                "submitted",
                "under_review",
                "verified",
            }
        ):
            return Response(
                {
                    "detail": (
                        "A verification request is "
                        "already active for this "
                        "organisation."
                    )
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        declaration_accurate = (
            request.data.get(
                "declaration_accurate",
                False,
            )
        )

        declaration_authorised = (
            request.data.get(
                "declaration_authorised",
                False,
            )
        )

        declaration_consent = (
            request.data.get(
                "declaration_consent",
                False,
            )
        )

        if not all(
            [
                declaration_accurate,
                declaration_authorised,
                declaration_consent,
            ]
        ):
            return Response(
                {
                    "detail": (
                        "All declarations must be "
                        "accepted before submitting "
                        "for verification."
                    )
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        verification = (
            PartnerVerificationRequest.objects.create(
                organisation=organisation,
                status="submitted",
                declaration_accurate=True,
                declaration_authorised=True,
                declaration_consent=True,
                submitted_by=request.user,
                submitted_at=timezone.now(),
            )
        )

        serializer = (
            PartnerVerificationRequestSerializer(
                verification,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class PartnerVerificationDocumentAPIView(APIView):
    """
    Upload verification evidence for a partner organisation.

    Only active owners/admins of the organisation may upload
    verification documents.
    """

    permission_classes = [
        IsAuthenticated,
        CanManagePartnerOrganisation,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    @transaction.atomic
    def post(
        self,
        request,
        organisation_id,
    ):
        organisation = get_user_partner_organisation(
            request.user,
            organisation_id,
        )

        self.check_object_permissions(
            request,
            organisation,
        )

        verification = (
            PartnerVerificationRequest.objects
            .filter(
                organisation=organisation,
            )
            .first()
        )

        # Allow evidence to be uploaded before final submission.
        # A draft verification request is created automatically
        # if one does not already exist.
        if verification is None:
            verification = (
                PartnerVerificationRequest.objects.create(
                    organisation=organisation,
                    status="draft",
                )
            )

        if verification.status in {
            "under_review",
            "verified",
        }:
            return Response(
                {
                    "detail": (
                        "Verification evidence cannot be changed "
                        "while this request is under review or "
                        "after it has been verified."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        document_type = request.data.get(
            "document_type",
        )

        title = (
            request.data.get("title")
            or ""
        ).strip()

        uploaded_file = request.FILES.get(
            "file",
        )

        valid_document_types = {
            choice[0]
            for choice
            in PartnerVerificationDocument.DOCUMENT_TYPE_CHOICES
        }

        if document_type not in valid_document_types:
            return Response(
                {
                    "document_type": (
                        "Please provide a valid document type."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not uploaded_file:
            return Response(
                {
                    "file": (
                        "Please select a file to upload."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 10 MB maximum.
        max_size = 10 * 1024 * 1024

        if uploaded_file.size > max_size:
            return Response(
                {
                    "file": (
                        "The uploaded file must not exceed 10 MB."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_extensions = {
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
        }

        suffix = Path(
            uploaded_file.name
        ).suffix.lower()

        if suffix not in allowed_extensions:
            return Response(
                {
                    "file": (
                        "Only PDF, JPG, JPEG and PNG files "
                        "are allowed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not title:
            title = uploaded_file.name

        document = (
            PartnerVerificationDocument.objects.create(
                verification_request=verification,
                document_type=document_type,
                title=title,
                file=uploaded_file,
                uploaded_by=request.user,
                is_active=True,
            )
        )

        serializer = (
            PartnerVerificationDocumentSerializer(
                document,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class PartnerVerificationDocumentDetailAPIView(APIView):
    """
    Delete verification evidence belonging to a partner
    organisation.
    """

    permission_classes = [
        IsAuthenticated,
        CanManagePartnerOrganisation,
    ]

    def delete(
        self,
        request,
        organisation_id,
        document_id,
    ):
        organisation = get_user_partner_organisation(
            request.user,
            organisation_id,
        )

        self.check_object_permissions(
            request,
            organisation,
        )

        document = get_object_or_404(
            PartnerVerificationDocument.objects
            .select_related(
                "verification_request",
            ),
            pk=document_id,
            verification_request__organisation=organisation,
            is_active=True,
        )

        verification = document.verification_request

        if verification.status in {
            "under_review",
            "verified",
        }:
            return Response(
                {
                    "detail": (
                        "Verification evidence cannot be removed "
                        "while this request is under review or "
                        "after it has been verified."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.file.delete(
            save=False,
        )

        document.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )



from .models import PartnerPreferences
from .serializers import PartnerPreferencesSerializer


class PartnerPreferencesAPIView(APIView):
    """
    Read and update authenticated partner workspace
    preferences.
    """

    permission_classes = [
        IsAuthenticated,
        CanManagePartnerOrganisation,
    ]

    def get(
        self,
        request,
        organisation_id,
    ):
        organisation = (
            get_user_partner_organisation(
                request.user,
                organisation_id,
            )
        )

        self.check_object_permissions(
            request,
            organisation,
        )

        preferences, _ = (
            PartnerPreferences.objects
            .get_or_create(
                organisation=organisation,
            )
        )

        serializer = (
            PartnerPreferencesSerializer(
                preferences,
            )
        )

        return Response(
            serializer.data,
        )

    @transaction.atomic
    def patch(
        self,
        request,
        organisation_id,
    ):
        organisation = (
            get_user_partner_organisation(
                request.user,
                organisation_id,
            )
        )

        self.check_object_permissions(
            request,
            organisation,
        )

        preferences, _ = (
            PartnerPreferences.objects
            .get_or_create(
                organisation=organisation,
            )
        )

        serializer = (
            PartnerPreferencesSerializer(
                preferences,
                data=request.data,
                partial=True,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        return Response(
            serializer.data,
        )
