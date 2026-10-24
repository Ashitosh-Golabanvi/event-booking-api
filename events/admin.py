
from django.contrib import admin

from .models import Booking, Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "city",
        "organizer",
        "start_datetime",
        "capacity",
        "ticket_price",
        "status",
    )

    list_filter = (
        "status",
        "city",
        "start_datetime",
    )

    search_fields = (
        "title",
        "description",
        "venue",
        "city",
        "organizer__username",
        "organizer__email",
    )

    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "booking_reference",
        "event",
        "attendee",
        "seats",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
        "event__city",
    )

    search_fields = (
        "booking_reference",
        "event__title",
        "attendee__username",
        "attendee__email",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "booking_reference",
        "created_at",
        "updated_at",
    )
