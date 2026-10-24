
from rest_framework import serializers

from .models import Booking


class OrganizerBookingSerializer(serializers.ModelSerializer):
    attendee_username = serializers.CharField(
        source="attendee.username",
        read_only=True,
    )
    attendee_email = serializers.EmailField(
        source="attendee.email",
        read_only=True,
    )

    class Meta:
        model = Booking
        fields = [
            "booking_reference",
            "attendee_username",
            "attendee_email",
            "seats",
            "status",
            "created_at",
        ]
        read_only_fields = fields
