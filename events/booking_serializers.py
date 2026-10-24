
from rest_framework import serializers

from .models import Booking, Event


class BookingCreateSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    seats = serializers.IntegerField(min_value=1, max_value=5)

    def validate_event_id(self, value):
        if not Event.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                "The selected event does not exist."
            )

        return value


class BookingSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(
        source="event.title",
        read_only=True,
    )
    event_start_datetime = serializers.DateTimeField(
        source="event.start_datetime",
        read_only=True,
    )

    class Meta:
        model = Booking
        fields = [
            "booking_reference",
            "event_title",
            "event_start_datetime",
            "seats",
            "status",
            "created_at",
        ]
        read_only_fields = fields
