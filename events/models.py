
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

import secrets
import string


class Event(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=200)
    description = models.TextField()
    venue = models.CharField(max_length=255)
    city = models.CharField(max_length=100)

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    capacity = models.PositiveIntegerField()
    ticket_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organized_events",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}

        if self.start_datetime and self.end_datetime:
            if self.end_datetime <= self.start_datetime:
                errors["end_datetime"] = (
                    "Event end time must be after the start time."
                )

        if self.capacity is not None and self.capacity < 1:
            errors["capacity"] = "Event capacity must be at least 1."

        if self.ticket_price is not None and self.ticket_price < 0:
            errors["ticket_price"] = "Ticket price cannot be negative."

        if (
            self.status == self.Status.PUBLISHED
            and self.start_datetime
            and self.start_datetime <= timezone.now()
        ):
            errors["start_datetime"] = (
                "A published event must start in the future."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title



class Booking(models.Model):

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    event = models.ForeignKey(
        Event,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    attendee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="event_bookings",
    )

    booking_reference = models.CharField(
        max_length=11,
        unique=True,
        editable=False,
    )

    seats = models.PositiveSmallIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(seats__gte=1)
                    & models.Q(seats__lte=5)
                ),
                name="booking_seats_between_1_and_5",
            ),
            models.UniqueConstraint(
                fields=["event", "attendee"],
                condition=models.Q(status="confirmed"),
                name="unique_confirmed_event_booking",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            alphabet = string.ascii_uppercase + string.digits

            while True:
                code = "BK-" + "".join(
                    secrets.choice(alphabet) for _ in range(8)
                )

                if not Booking.objects.filter(
                    booking_reference=code
                ).exists():
                    self.booking_reference = code
                    break

        super().save(*args, **kwargs)

    def __str__(self):
        return self.booking_reference
