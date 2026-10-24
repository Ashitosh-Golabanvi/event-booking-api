
from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "city",
        "start_datetime",
        "capacity",
        "ticket_price",
        "status",
        "organizer",
    )

    list_filter = ("status", "city", "start_datetime")
    search_fields = ("title", "description", "venue", "city")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
