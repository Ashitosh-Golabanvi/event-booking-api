
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from events.models import Booking, Event


User = get_user_model()


class Command(BaseCommand):
    help = "Create reusable demo users, events, and bookings."

    @transaction.atomic
    def handle(self, *args, **options):
        # Create or reuse demo users.
        organizer1 = self.get_user(
            username="demo_organizer",
            email="organizer@example.com",
            role=User.Role.ORGANIZER,
            first_name="Demo",
            last_name="Organizer",
        )

        organizer2 = self.get_user(
            username="demo_organizer2",
            email="organizer2@example.com",
            role=User.Role.ORGANIZER,
            first_name="Second",
            last_name="Organizer",
        )

        attendee1 = self.get_user(
            username="demo_attendee",
            email="attendee@example.com",
            role=User.Role.ATTENDEE,
            first_name="Demo",
            last_name="Attendee",
        )

        attendee2 = self.get_user(
            username="demo_attendee2",
            email="attendee2@example.com",
            role=User.Role.ATTENDEE,
            first_name="Second",
            last_name="Attendee",
        )

        attendee3 = self.get_user(
            username="demo_attendee3",
            email="attendee3@example.com",
            role=User.Role.ATTENDEE,
            first_name="Third",
            last_name="Attendee",
        )

        now = timezone.now()

        # Create or reuse upcoming published events.
        event1 = self.get_event(
            title="Django Backend Development Workshop",
            defaults={
                "description": (
                    "A practical workshop covering Django, DRF, "
                    "REST APIs, and backend development."
                ),
                "venue": "Tech Hub",
                "city": "Bengaluru",
                "start_datetime": now + timedelta(days=14),
                "end_datetime": now + timedelta(days=14, hours=3),
                "capacity": 30,
                "ticket_price": Decimal("499.00"),
                "status": Event.Status.PUBLISHED,
                "organizer": organizer1,
            },
        )

        event2 = self.get_event(
            title="Python Community Meetup",
            defaults={
                "description": (
                    "A community meetup for Python developers "
                    "to share projects and ideas."
                ),
                "venue": "Innovation Center",
                "city": "Bengaluru",
                "start_datetime": now + timedelta(days=21),
                "end_datetime": now + timedelta(days=21, hours=2),
                "capacity": 50,
                "ticket_price": Decimal("0.00"),
                "status": Event.Status.PUBLISHED,
                "organizer": organizer2,
            },
        )

        # Create or reuse a draft event.
        draft_event = self.get_event(
            title="Advanced API Design Session",
            defaults={
                "description": (
                    "A planned session on API design and performance."
                ),
                "venue": "Developer Space",
                "city": "Pune",
                "start_datetime": now + timedelta(days=30),
                "end_datetime": now + timedelta(days=30, hours=2),
                "capacity": 25,
                "ticket_price": Decimal("299.00"),
                "status": Event.Status.DRAFT,
                "organizer": organizer1,
            },
        )

        # Create or reuse confirmed bookings.
        self.get_booking(event1, attendee1, seats=2)
        self.get_booking(event1, attendee2, seats=1)
        self.get_booking(event2, attendee2, seats=2)
        self.get_booking(event2, attendee3, seats=1)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data is ready: 2 organizers, 3 attendees, "
                "3 events, and up to 4 confirmed bookings."
            )
        )
        self.stdout.write(
            "Demo login usernames: demo_organizer, demo_organizer2, "
            "demo_attendee, demo_attendee2, demo_attendee3"
        )
        self.stdout.write(
            "Demo password for newly created users: DemoPass123!"
        )
        self.stdout.write(
            f"Draft event available for testing: {draft_event.title}"
        )


    def get_user(self, username, email, role, first_name, last_name):
        # First, find a user by the demo username.
        user = User.objects.filter(username=username).first()

        # If the username does not exist, check whether the email
        # already belongs to another user.
        if user is None:
            user = User.objects.filter(email__iexact=email).first()

        if user is not None:
            self.stdout.write(
                f"Reusing existing user: {user.username}"
            )
            return user

        # Create a new user only when neither username nor email exists.
        user = User(
            username=username,
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password("DemoPass123!")
        user.save()

        self.stdout.write(f"Created demo user: {username}")
        return user


    def get_event(self, title, defaults):
        event, created = Event.objects.get_or_create(
            title=title,
            defaults=defaults,
        )

        action = "Created" if created else "Reusing"
        self.stdout.write(f"{action} event: {title}")

        return event

    def get_booking(self, event, attendee, seats):
        booking, created = Booking.objects.get_or_create(
            event=event,
            attendee=attendee,
            status=Booking.Status.CONFIRMED,
            defaults={"seats": seats},
        )

        action = "Created" if created else "Reusing"
        self.stdout.write(
            f"{action} booking for {attendee.username}: "
            f"{event.title} ({booking.seats} seat(s))"
        )

        return booking
