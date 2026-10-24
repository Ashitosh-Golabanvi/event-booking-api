
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Booking, Event

User = get_user_model()


class EventBookingAPITests(APITestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="test_organizer",
            email="organizer@example.com",
            password="StrongTestPass!927",
            role=User.Role.ORGANIZER,
        )
        self.other_organizer = User.objects.create_user(
            username="other_organizer",
            email="other_organizer@example.com",
            password="StrongTestPass!927",
            role=User.Role.ORGANIZER,
        )
        self.attendee = User.objects.create_user(
            username="test_attendee",
            email="attendee@example.com",
            password="StrongTestPass!927",
            role=User.Role.ATTENDEE,
        )

        self.event = Event.objects.create(
            title="Django Testing Workshop",
            description="Learn Django API testing",
            venue="Tech Park",
            city="Bengaluru",
            start_datetime=timezone.now() + timedelta(days=10),
            end_datetime=timezone.now() + timedelta(days=10, hours=2),
            capacity=5,
            ticket_price=Decimal("0.00"),
            organizer=self.organizer,
        )

        self.events_url = "/api/events/"
        self.bookings_url = "/api/events/bookings/"

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_attendee_cannot_create_event(self):
        self.authenticate(self.attendee)

        response = self.client.post(
            self.events_url,
            {
                "title": "Unauthorized Event",
                "description": "Should not be created",
                "venue": "Venue",
                "city": "Bengaluru",
                "start_datetime": (
                    timezone.now() + timedelta(days=5)
                ).isoformat(),
                "end_datetime": (
                    timezone.now() + timedelta(days=5, hours=2)
                ).isoformat(),
                "capacity": 10,
                "ticket_price": "0.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_public_event_list_excludes_drafts(self):
        response = self.client.get(self.events_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_organizer_can_publish_own_future_event(self):
        self.authenticate(self.organizer)

        response = self.client.post(
            f"{self.events_url}{self.event.id}/publish/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.event.refresh_from_db()
        self.assertEqual(self.event.status, Event.Status.PUBLISHED)

    def test_organizer_cannot_publish_another_organizers_event(self):
        self.authenticate(self.other_organizer)

        response = self.client.post(
            f"{self.events_url}{self.event.id}/publish/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_attendee_can_book_published_event(self):
        self.event.status = Event.Status.PUBLISHED
        self.event.save(update_fields=["status", "updated_at"])
        self.authenticate(self.attendee)

        response = self.client.post(
            self.bookings_url,
            {"event_id": self.event.id, "seats": 2},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(response.data["seats"], 2)
        self.assertTrue(response.data["booking_reference"].startswith("BK-"))
        self.assertEqual(Booking.objects.count(), 1)

    def test_duplicate_confirmed_booking_is_rejected(self):
        self.event.status = Event.Status.PUBLISHED
        self.event.save(update_fields=["status", "updated_at"])

        Booking.objects.create(
            event=self.event,
            attendee=self.attendee,
            seats=1,
        )

        self.authenticate(self.attendee)

        response = self.client.post(
            self.bookings_url,
            {"event_id": self.event.id, "seats": 1},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Booking.objects.count(), 1)

    def test_booking_cannot_exceed_remaining_capacity(self):
        self.event.status = Event.Status.PUBLISHED
        self.event.capacity = 2
        self.event.save(update_fields=["status", "capacity", "updated_at"])

        another_attendee = User.objects.create_user(
            username="another_attendee",
            email="another_attendee@example.com",
            password="StrongTestPass!927",
            role=User.Role.ATTENDEE,
        )

        Booking.objects.create(
            event=self.event,
            attendee=another_attendee,
            seats=2,
        )

        self.authenticate(self.attendee)

        response = self.client.post(
            self.bookings_url,
            {"event_id": self.event.id, "seats": 1},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(response.data["remaining_seats"], 0)

    def test_attendee_can_cancel_booking_more_than_24_hours_before_event(self):
        self.event.status = Event.Status.PUBLISHED
        self.event.save(update_fields=["status", "updated_at"])

        booking = Booking.objects.create(
            event=self.event,
            attendee=self.attendee,
            seats=1,
        )

        self.authenticate(self.attendee)

        response = self.client.post(
            f"{self.bookings_url}{booking.booking_reference}/cancel/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)

    def test_attendee_cannot_cancel_another_users_booking(self):
        self.event.status = Event.Status.PUBLISHED
        self.event.save(update_fields=["status", "updated_at"])

        booking = Booking.objects.create(
            event=self.event,
            attendee=self.attendee,
            seats=1,
        )

        self.authenticate(self.other_organizer)

        response = self.client.post(
            f"{self.bookings_url}{booking.booking_reference}/cancel/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    
    def test_booking_rejects_more_than_five_seats(self):
        self.event.status = Event.Status.PUBLISHED
        self.event.save(update_fields=["status", "updated_at"])
        self.authenticate(self.attendee)

        response = self.client.post(
            self.bookings_url,
            {"event_id": self.event.id, "seats": 6},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Booking.objects.count(), 0)

    def test_booking_rejects_zero_seats(self):
        self.event.status = Event.Status.PUBLISHED
        self.event.save(update_fields=["status", "updated_at"])
        self.authenticate(self.attendee)

        response = self.client.post(
            self.bookings_url,
            {"event_id": self.event.id, "seats": 0},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Booking.objects.count(), 0)

    def test_booking_cannot_be_cancelled_within_24_hours(self):
        self.event.status = Event.Status.PUBLISHED
        self.event.start_datetime = timezone.now() + timedelta(hours=12)
        self.event.end_datetime = self.event.start_datetime + timedelta(hours=2)
        self.event.save(
            update_fields=[
                "status",
                "start_datetime",
                "end_datetime",
                "updated_at",
            ]
        )

        booking = Booking.objects.create(
            event=self.event,
            attendee=self.attendee,
            seats=1,
        )

        self.authenticate(self.attendee)

        response = self.client.post(
            f"{self.bookings_url}{booking.booking_reference}/cancel/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_published_event_cannot_be_edited(self):
        self.event.status = Event.Status.PUBLISHED
        self.event.save(update_fields=["status", "updated_at"])
        self.authenticate(self.organizer)

        response = self.client.put(
            f"{self.events_url}{self.event.id}/manage/",
            {
                "title": "Updated Workshop",
                "description": "Updated description",
                "venue": "Updated venue",
                "city": "Bengaluru",
                "start_datetime": (
                    timezone.now() + timedelta(days=10)
                ).isoformat(),
                "end_datetime": (
                    timezone.now() + timedelta(days=10, hours=2)
                ).isoformat(),
                "capacity": 5,
                "ticket_price": "0.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Django Testing Workshop")

    def test_published_event_cannot_be_deleted(self):
        self.event.status = Event.Status.PUBLISHED
        self.event.save(update_fields=["status", "updated_at"])
        self.authenticate(self.organizer)

        response = self.client.delete(
            f"{self.events_url}{self.event.id}/manage/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())

    
    def test_organizer_cannot_delete_another_organizers_draft(self):
        self.authenticate(self.other_organizer)

        response = self.client.delete(
            f"{self.events_url}{self.event.id}/manage/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())


