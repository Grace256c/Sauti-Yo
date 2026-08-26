from django.contrib.auth import (
    authenticate,
    login,
    logout,
)
from django.middleware.csrf import get_token

from rest_framework import status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.partners.models import PartnerMember

from .serializers import PartnerLoginSerializer


def build_partner_session_data(user, membership):
    return {
        "user": {
            "id": user.id,
            "username": user.get_username(),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        "membership": {
            "id": membership.id,
            "role": membership.role,
            "organisation_id": membership.organisation_id,
            "organisation_name": (
                membership.organisation.support_service.name
            ),
        },
    }


class CSRFTokenAPIView(APIView):
    """
    Return a CSRF token for the React frontend.

    Calling this endpoint also causes Django to set the
    CSRF cookie used for protected requests.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        token = get_token(request)

        return Response(
            {
                "csrfToken": token,
            }
        )


class PartnerLoginAPIView(APIView):
    """
    Authenticate a partner user and create a Django session.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PartnerLoginSerializer(
            data=request.data
        )
        serializer.is_valid(
            raise_exception=True
        )

        user = authenticate(
            request=request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            return Response(
                {
                    "detail": (
                        "Invalid username or password."
                    )
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        membership = (
            PartnerMember.objects
            .select_related(
                "organisation",
                "organisation__support_service",
            )
            .filter(
                user=user,
                is_active=True,
                organisation__is_active=True,
            )
            .order_by("id")
            .first()
        )

        if membership is None:
            return Response(
                {
                    "detail": (
                        "This account is not connected to "
                        "an active partner organisation."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        login(
            request,
            user,
        )

        return Response(
            build_partner_session_data(
                user,
                membership,
            ),
            status=status.HTTP_200_OK,
        )


class PartnerLogoutAPIView(APIView):
    """
    Destroy the current authenticated partner session.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)

        return Response(
            {
                "detail": (
                    "Logged out successfully."
                )
            },
            status=status.HTTP_200_OK,
        )


class PartnerSessionAPIView(APIView):
    """
    Return the currently authenticated partner account
    and active organisation membership.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = (
            PartnerMember.objects
            .select_related(
                "organisation",
                "organisation__support_service",
            )
            .filter(
                user=request.user,
                is_active=True,
                organisation__is_active=True,
            )
            .order_by("id")
            .first()
        )

        if membership is None:
            return Response(
                {
                    "detail": (
                        "This account is not connected to "
                        "an active partner organisation."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            build_partner_session_data(
                request.user,
                membership,
            ),
            status=status.HTTP_200_OK,
        )
