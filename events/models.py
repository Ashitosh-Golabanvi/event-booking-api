
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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
