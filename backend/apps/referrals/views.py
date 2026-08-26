from uuid import uuid4
from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.partners.models import PartnerMember
from apps.partners.permissions import CanManageReferrals

from .models import (
    Referral,
    ReferralStatusHistory,
)
from .serializers import (
    ReferralCreateSerializer,
    ReferralSerializer,
)


def get_user_partner_organisation_ids(user):
    return PartnerMember.objects.filter(
        user=user,
        is_active=True,
        organisation__is_active=True,
    ).values_list(
        "organisation_id",
        flat=True,
    )


class ReferralListAPIView(ListAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [
        IsAuthenticated,
        CanManageReferrals,
    ]

    def get_queryset(self):
        organisation_ids = (
            get_user_partner_organisation_ids(
                self.request.user
            )
        )

        queryset = (
            Referral.objects
            .filter(
                organisation_id__in=organisation_ids
            )
            .select_related(
                "organisation",
                "organisation__support_service",
                "rights_topic",
                "assigned_to",
            )
            .prefetch_related(
                "status_history",
                "status_history__changed_by",
            )
        )

        status_value = (
            self.request.query_params.get(
                "status"
            )
        )

        organisation_id = (
            self.request.query_params.get(
                "organisation"
            )
        )

        if status_value:
            queryset = queryset.filter(
                status=status_value
            )

        if organisation_id:
            queryset = queryset.filter(
                organisation_id=organisation_id
            )

        return queryset


class ReferralDetailAPIView(RetrieveAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [
        IsAuthenticated,
        CanManageReferrals,
    ]

    def get_queryset(self):
        organisation_ids = (
            get_user_partner_organisation_ids(
                self.request.user
            )
        )

        return (
            Referral.objects
            .filter(
                organisation_id__in=organisation_ids
            )
            .select_related(
                "organisation",
                "organisation__support_service",
                "rights_topic",
                "assigned_to",
            )
            .prefetch_related(
                "status_history",
                "status_history__changed_by",
            )
        )


class ReferralCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    @transaction.atomic
    def post(self, request):
        serializer = ReferralCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        organisation = serializer.validated_data[
            "organisation"
        ]

        membership_exists = (
            PartnerMember.objects.filter(
                user=request.user,
                organisation=organisation,
                role__in={
                    "owner",
                    "admin",
                    "case_worker",
                },
                is_active=True,
            ).exists()
        )

        if not membership_exists:
            return Response(
                {
                    "detail": (
                        "You do not have permission "
                        "to create referrals for "
                        "this organisation."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        referral = serializer.save(
            reference=self._generate_reference(),
            status="new",
            shared_at=timezone.now(),
        )

        ReferralStatusHistory.objects.create(
            referral=referral,
            from_status="",
            to_status="new",
            changed_by=request.user,
            note="Referral created.",
        )

        output = ReferralSerializer(
            referral,
            context={
                "request": request,
            },
        )

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )

    def _generate_reference(self):
        return (
            f"SY-REF-{uuid4().hex[:12].upper()}"
        )


class ReferralStatusUpdateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        CanManageReferrals,
    ]

    ALLOWED_TRANSITIONS = {
        "new": {
            "reviewing",
            "declined",
            "cancelled",
        },
        "reviewing": {
            "accepted",
            "declined",
            "cancelled",
        },
        "accepted": {
            "in_progress",
            "cancelled",
        },
        "in_progress": {
            "completed",
            "closed",
        },
        "completed": {
            "closed",
        },
        "declined": set(),
        "cancelled": set(),
        "closed": set(),
    }

    @transaction.atomic
    def post(
        self,
        request,
        pk,
    ):
        organisation_ids = (
            get_user_partner_organisation_ids(
                request.user
            )
        )

        try:
            referral = (
                Referral.objects
                .select_for_update()
                .get(
                    pk=pk,
                    organisation_id__in=organisation_ids,
                )
            )
        except Referral.DoesNotExist:
            return Response(
                {
                    "detail":
                        "Referral not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = (
            PartnerMember.objects.filter(
                user=request.user,
                organisation=referral.organisation,
                is_active=True,
            ).first()
        )

        if (
            membership is None
            or membership.role
            not in {
                "owner",
                "admin",
                "case_worker",
            }
        ):
            return Response(
                {
                    "detail": (
                        "You do not have permission "
                        "to update this referral."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status = request.data.get(
            "status"
        )

        note = request.data.get(
            "note",
            "",
        )

        if not new_status:
            return Response(
                {
                    "status":
                        "A new referral status is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_statuses = {
            choice[0]
            for choice
            in Referral.STATUS_CHOICES
        }

        if new_status not in valid_statuses:
            return Response(
                {
                    "status":
                        "Invalid referral status."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_status = referral.status

        allowed = (
            self.ALLOWED_TRANSITIONS.get(
                current_status,
                set(),
            )
        )

        if new_status not in allowed:
            return Response(
                {
                    "status": (
                        "Cannot move referral "
                        f"from '{current_status}' "
                        f"to '{new_status}'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        referral.status = new_status

        if new_status == "accepted":
            referral.accepted_at = timezone.now()

        if new_status == "completed":
            referral.completed_at = timezone.now()

        referral.save()

        ReferralStatusHistory.objects.create(
            referral=referral,
            from_status=current_status,
            to_status=new_status,
            changed_by=request.user,
            note=note,
        )

        output = ReferralSerializer(
            referral,
            context={
                "request": request,
            },
        )

        return Response(
            output.data,
            status=status.HTTP_200_OK,
        )


from rest_framework.permissions import AllowAny

from apps.partners.models import (
    PartnerOrganisation,
    PartnerVerificationRequest,
)

from .serializers import CitizenReferralCreateSerializer


class CitizenReferralCreateAPIView(APIView):
    """
    Creates a consented citizen referral to an eligible,
    verified partner organisation.
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(
        self,
        request,
    ):
        serializer = CitizenReferralCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        organisation = serializer.validated_data[
            "organisation"
        ]

        organisation = (
            PartnerOrganisation.objects
            .select_related(
                "service_configuration",
            )
            .filter(
                pk=organisation.pk,
                is_active=True,
            )
            .first()
        )

        if organisation is None:
            return Response(
                {
                    "detail":
                        "This support provider is not available."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        configuration = getattr(
            organisation,
            "service_configuration",
            None,
        )

        if (
            configuration is None
            or not configuration.accepting_referrals
        ):
            return Response(
                {
                    "detail":
                        "This support provider is not currently accepting referrals."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        verified = (
            PartnerVerificationRequest.objects
            .filter(
                organisation=organisation,
                status="verified",
            )
            .exists()
        )

        if not verified:
            return Response(
                {
                    "detail":
                        "This support provider is not currently eligible for citizen referrals."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        referral = serializer.save(
            reference=self._generate_reference(),
            status="new",
            shared_at=timezone.now(),
        )

        ReferralStatusHistory.objects.create(
            referral=referral,
            from_status="",
            to_status="new",
            changed_by=None,
            note="Citizen referral created with consent.",
        )

        output = ReferralSerializer(
            referral,
            context={
                "request": request,
            },
        )

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )

    def _generate_reference(self):
        return (
            f"SY-REF-{uuid4().hex[:12].upper()}"
        )
