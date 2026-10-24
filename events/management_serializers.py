from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from .models import Booking, Event


class EventUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "venue",
            "city",
            "start_datetime",
            "end_datetime",
            "capacity",
            "ticket_price",
        ]

    def validate(self, attrs):
        event = self.instance

        start_datetime = attrs.get(
            "start_datetime",
            event.start_datetime,
        )
        end_datetime = attrs.get(
            "end_datetime",
            event.end_datetime,
        )
        capacity = attrs.get("capacity", event.capacity)
        ticket_price = attrs.get(
            "ticket_price",
            event.ticket_price,
        )

        if end_datetime <= start_datetime:
            raise serializers.ValidationError({
                "end_datetime": "Event end time must be after start time."
            })

        if capacity < 1:
            raise serializers.ValidationError({
                "capacity": "Capacity must be at least 1."
            })

        if ticket_price < 0:
            raise serializers.ValidationError({
                "ticket_price": "Ticket price cannot be negative."
            })

        if (
            event.status == Event.Status.DRAFT
            and start_datetime <= timezone.now()
        ):
            raise serializers.ValidationError({
                "start_datetime": "The event must start in the future."
            })
        
        booked_seats = Booking.objects.filter(
            event=event,
            status=Booking.Status.CONFIRMED,
        ).aggregate(total=Sum("seats"))["total"] or 0

        if capacity < booked_seats:
            raise serializers.ValidationError({
                "capacity": (
                    f"Capacity cannot be lower than the "
                    f"{booked_seats} already-booked seats."
                )
            })

        return attrs
