from rest_framework.permissions import BasePermission

from .models import PartnerMember


class IsAuthenticatedPartnerMember(BasePermission):
    """
    Allows access only to authenticated users who belong
    to at least one active partner organisation.
    """

    message = (
        "You must be an active member of a partner "
        "organisation to access this resource."
    )

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return PartnerMember.objects.filter(
            user=request.user,
            is_active=True,
            organisation__is_active=True,
        ).exists()


class IsPartnerOrganisationMember(BasePermission):
    """
    Object-level permission for partner organisations.
    """

    message = (
        "You do not have permission to access this "
        "partner organisation."
    )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        if not request.user.is_authenticated:
            return False

        return PartnerMember.objects.filter(
            user=request.user,
            organisation=obj,
            is_active=True,
            organisation__is_active=True,
        ).exists()


class CanManagePartnerOrganisation(BasePermission):
    """
    Allows organisation management only to owners
    and administrators.
    """

    allowed_roles = {
        "owner",
        "admin",
    }

    message = (
        "Only partner owners or administrators can "
        "manage organisation settings."
    )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        if not request.user.is_authenticated:
            return False

        return PartnerMember.objects.filter(
            user=request.user,
            organisation=obj,
            role__in=self.allowed_roles,
            is_active=True,
            organisation__is_active=True,
        ).exists()


class CanManageReferrals(BasePermission):
    """
    Owners, admins and case workers may manage referrals.
    Viewers can read but should not change referral state.
    """

    writable_roles = {
        "owner",
        "admin",
        "case_worker",
    }

    message = (
        "You do not have permission to manage referrals "
        "for this organisation."
    )

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.method in {
            "GET",
            "HEAD",
            "OPTIONS",
        }:
            return PartnerMember.objects.filter(
                user=request.user,
                is_active=True,
                organisation__is_active=True,
            ).exists()

        return PartnerMember.objects.filter(
            user=request.user,
            role__in=self.writable_roles,
            is_active=True,
            organisation__is_active=True,
        ).exists()