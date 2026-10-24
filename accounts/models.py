
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ORGANIZER = "organizer", "Organizer"
        ATTENDEE = "attendee", "Attendee"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ATTENDEE,
    )

    def __str__(self):
        return self.username
