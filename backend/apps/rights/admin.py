from django.contrib import admin

from .models import (
    ActionStep,
    RightsTopic,
    SafetyResponse,
    Situation,
    SituationRightsTopic,
)


class ActionStepInline(admin.TabularInline):
    model = ActionStep
    extra = 0


class SafetyResponseInline(admin.TabularInline):
    model = SafetyResponse
    extra = 0


@admin.register(Situation)
class SituationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "risk_level",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "risk_level",
        "is_active",
    )

    search_fields = (
        "title",
        "description",
    )

    prepopulated_fields = {
        "slug": ("title",),
    }


@admin.register(RightsTopic)
class RightsTopicAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "risk_level",
        "verification_status",
        "reviewed_by",
        "last_reviewed",
        "is_active",
    )

    list_filter = (
        "risk_level",
        "verification_status",
        "is_active",
    )

    search_fields = (
        "title",
        "summary",
        "source_name",
    )

    prepopulated_fields = {
        "slug": ("title",),
    }

    filter_horizontal = (
        "support_services",
    )

    inlines = [
        ActionStepInline,
        SafetyResponseInline,
    ]


@admin.register(SituationRightsTopic)
class SituationRightsTopicAdmin(admin.ModelAdmin):
    list_display = (
        "situation",
        "rights_topic",
        "created_at",
    )

    search_fields = (
        "situation__title",
        "rights_topic__title",
    )


@admin.register(ActionStep)
class ActionStepAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "rights_topic",
        "order",
        "is_safety_critical",
        "is_active",
    )

    list_filter = (
        "is_safety_critical",
        "is_active",
    )

    search_fields = (
        "title",
        "description",
        "rights_topic__title",
    )


@admin.register(SafetyResponse)
class SafetyResponseAdmin(admin.ModelAdmin):
    list_display = (
        "rights_topic",
        "trigger_key",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "trigger_key",
        "message",
        "rights_topic__title",
    )