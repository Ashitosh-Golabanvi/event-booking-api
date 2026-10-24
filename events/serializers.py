
from django.utils import timezone
from rest_framework import serializers

from .models import Event


class EventSerializer(serializers.ModelSerializer):

    organizer = serializers.ReadOnlyField(source="organizer.username")

    booked_seats = serializers.IntegerField(read_only=True)
    remaining_seats = serializers.IntegerField(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "venue",
            "city",
            "start_datetime",
            "end_datetime",
            "capacity",
            "ticket_price",
            "status",
            "organizer",
            "booked_seats",
            "remaining_seats",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "organizer",
            "booked_seats",
            "remaining_seats",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        start_datetime = attrs.get(
            "start_datetime",
            getattr(self.instance, "start_datetime", None),
        )
        end_datetime = attrs.get(
            "end_datetime",
            getattr(self.instance, "end_datetime", None),
        )
        capacity = attrs.get(
            "capacity",
            getattr(self.instance, "capacity", None),
        )
        ticket_price = attrs.get(
            "ticket_price",
            getattr(self.instance, "ticket_price", 0),
        )

        errors = {}

        if (
            start_datetime
            and end_datetime
            and end_datetime <= start_datetime
        ):
            errors["end_datetime"] = (
                "Event end time must be after the start time."
            )

        if start_datetime and start_datetime <= timezone.now():
            if self.instance is None:
                errors["start_datetime"] = (
                    "Event start time must be in the future."
                )

        if capacity is not None and capacity < 1:
            errors["capacity"] = "Capacity must be at least 1."

        if ticket_price is not None and ticket_price < 0:
            errors["ticket_price"] = (
                "Ticket price cannot be negative."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs
