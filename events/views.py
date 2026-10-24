from datetime import timedelta
from django.db import transaction
from django.db.models import F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .booking_serializers import (
    BookingCreateSerializer,
    BookingSerializer,
)
from .models import Booking, Event
from .permissions import IsOrganizer
from .serializers import EventSerializer
from django.db.models import Sum
from rest_framework import serializers
from .management_serializers import EventUpdateSerializer
from .pagination import EventPagination
from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from django.db.models import Count
from .organizer_serializers import OrganizerBookingSerializer


def event_queryset():
    return Event.objects.annotate(
        booked_seats=Coalesce(
            Sum(
                "bookings__seats",
                filter=Q(bookings__status=Booking.Status.CONFIRMED),
            ),
            Value(0),
            output_field=IntegerField(),
        )
    ).annotate(
        remaining_seats=F("capacity") - F("booked_seats")
    )



class EventListCreateView(generics.ListCreateAPIView):
    serializer_class = EventSerializer
    pagination_class = EventPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsOrganizer()]

        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = event_queryset()

        if self.request.method == "POST":
            return queryset.none()

        queryset = queryset.filter(
            status=Event.Status.PUBLISHED,
            start_datetime__gt=timezone.now(),
        )

        params = self.request.query_params

        city = params.get("city")
        if city:
            queryset = queryset.filter(city__iexact=city.strip())

        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
            )

        start_date = params.get("start_date")
        if start_date:
            parsed_start = parse_date(start_date)
            if parsed_start is None:
                raise ValidationError({
                    "start_date": "Use YYYY-MM-DD format."
                })

            queryset = queryset.filter(
                start_datetime__date__gte=parsed_start
            )

        end_date = params.get("end_date")
        if end_date:
            parsed_end = parse_date(end_date)
            if parsed_end is None:
                raise ValidationError({
                    "end_date": "Use YYYY-MM-DD format."
                })

            queryset = queryset.filter(
                start_datetime__date__lte=parsed_end
            )

        min_price = params.get("min_price")
        if min_price is not None:
            try:
                value = Decimal(min_price)
                if not value.is_finite() or value < 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                raise ValidationError({
                    "min_price": "Enter a valid non-negative price."
                })

            queryset = queryset.filter(ticket_price__gte=value)

        max_price = params.get("max_price")
        if max_price is not None:
            try:
                value = Decimal(max_price)
                if not value.is_finite() or value < 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                raise ValidationError({
                    "max_price": "Enter a valid non-negative price."
                })

            queryset = queryset.filter(ticket_price__lte=value)

        if min_price is not None and max_price is not None:
            if Decimal(min_price) > Decimal(max_price):
                raise ValidationError({
                    "price": "min_price cannot exceed max_price."
                })

        is_free = params.get("is_free")
        if is_free is not None:
            if is_free.lower() == "true":
                queryset = queryset.filter(ticket_price=0)
            elif is_free.lower() == "false":
                queryset = queryset.filter(ticket_price__gt=0)
            else:
                raise ValidationError({
                    "is_free": "Use true or false."
                })

        ordering = params.get("ordering", "start_datetime")
        allowed_ordering = {
            "start_datetime",
            "-start_datetime",
            "ticket_price",
            "-ticket_price",
        }

        if ordering not in allowed_ordering:
            raise ValidationError({
                "ordering": (
                    "Use start_datetime, -start_datetime, "
                    "ticket_price, or -ticket_price."
                )
            })

        return queryset.order_by(ordering, "id")

    def perform_create(self, serializer):
        user = self.request.user

        if not (user.is_superuser or user.role == "organizer"):
            raise PermissionDenied(
                "Only organizers can create events."
            )

        serializer.save(organizer=user)



class EventDetailView(generics.RetrieveAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = event_queryset()
        user = self.request.user

        if user.is_authenticated and (
            user.is_superuser or user.role == "organizer"
        ):
            return queryset.filter(
                Q(status=Event.Status.PUBLISHED)
                | Q(organizer=user)
            )

        return queryset.filter(
            status=Event.Status.PUBLISHED,
            start_datetime__gt=timezone.now(),
        )


class BookingListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(
            attendee=request.user
        ).select_related("event").order_by("-created_at")

        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    def post(self, request):
        if (
            request.user.is_superuser
            or request.user.role != "attendee"
        ):
            return Response(
                {"error": "Only attendees can book events."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_id = serializer.validated_data["event_id"]
        seats = serializer.validated_data["seats"]

        with transaction.atomic():
            event = get_object_or_404(
                Event.objects.select_for_update(),
                pk=event_id,
            )

            if event.status != Event.Status.PUBLISHED:
                return Response(
                    {"error": "This event is not available for booking."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if event.start_datetime <= timezone.now():
                return Response(
                    {"error": "This event has already started."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            already_booked = Booking.objects.filter(
                event=event,
                attendee=request.user,
                status=Booking.Status.CONFIRMED,
            ).exists()

            if already_booked:
                return Response(
                    {
                        "error": (
                            "You already have a confirmed booking "
                            "for this event."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            booked_seats = Booking.objects.filter(
                event=event,
                status=Booking.Status.CONFIRMED,
            ).aggregate(total=Sum("seats"))["total"] or 0

            remaining_seats = event.capacity - booked_seats

            if seats > remaining_seats:
                return Response(
                    {
                        "error": "Not enough seats available.",
                        "remaining_seats": remaining_seats,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            booking = Booking.objects.create(
                event=event,
                attendee=request.user,
                seats=seats,
            )

        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_201_CREATED,
        )


class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_reference):
        with transaction.atomic():
            booking = get_object_or_404(
                Booking.objects.select_for_update().select_related("event"),
                booking_reference=booking_reference,
                attendee=request.user,
            )

            if booking.status != Booking.Status.CONFIRMED:
                return Response(
                    {"error": "This booking is already cancelled."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cutoff = (
                booking.event.start_datetime - timedelta(hours=24)
            )

            if timezone.now() > cutoff:
                return Response(
                    {
                        "error": (
                            "Bookings can only be cancelled at least "
                            "24 hours before the event."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            booking.status = Booking.Status.CANCELLED
            booking.save(update_fields=["status", "updated_at"])

        return Response(
            {"message": "Booking cancelled successfully."},
            status=status.HTTP_200_OK,
        )



class EventManageDetailView(generics.GenericAPIView):
    serializer_class = EventUpdateSerializer
    permission_classes = [IsAuthenticated, IsOrganizer]

    def get_queryset(self):
        return Event.objects.all()

    def get_object(self):
        event = get_object_or_404(
            self.get_queryset(),
            pk=self.kwargs["pk"],
        )

        if (
            not self.request.user.is_superuser
            and event.organizer_id != self.request.user.id
        ):
            raise PermissionDenied(
                "You can manage only your own events."
            )

        return event

    def put(self, request, pk):
        event = self.get_object()

        if event.status != Event.Status.DRAFT:
            return Response(
                {
                    "error": (
                        "Only draft events can be edited. "
                        "Published events can only be cancelled."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            event,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            EventSerializer(event, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        event = self.get_object()

        if event.status != Event.Status.DRAFT:
            return Response(
                {"error": "Only draft events can be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class EventPublishView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizer]

    def post(self, request, pk):
        with transaction.atomic():
            event = get_object_or_404(
                Event.objects.select_for_update(),
                pk=pk,
            )

            if (
                not request.user.is_superuser
                and event.organizer_id != request.user.id
            ):
                raise PermissionDenied(
                    "You can manage only your own events."
                )

            if event.status != Event.Status.DRAFT:
                return Response(
                    {"error": "Only draft events can be published."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if event.start_datetime <= timezone.now():
                return Response(
                    {"error": "The event must start in the future."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if event.end_datetime <= event.start_datetime:
                return Response(
                    {
                        "error": (
                            "Event end time must be after start time."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if event.capacity < 1:
                return Response(
                    {"error": "Capacity must be at least 1."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            event.status = Event.Status.PUBLISHED
            event.full_clean()
            event.save(update_fields=["status", "updated_at"])

        return Response(
            EventSerializer(
                event,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )


class EventCancelView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizer]

    def post(self, request, pk):
        with transaction.atomic():
            event = get_object_or_404(
                Event.objects.select_for_update(),
                pk=pk,
            )

            if (
                not request.user.is_superuser
                and event.organizer_id != request.user.id
            ):
                raise PermissionDenied(
                    "You can manage only your own events."
                )

            if event.status != Event.Status.PUBLISHED:
                return Response(
                    {
                        "error": (
                            "Only published events can be cancelled."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            event.status = Event.Status.CANCELLED
            event.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "message": "Event cancelled successfully.",
                "event_id": event.id,
                "status": event.status,
            },
            status=status.HTTP_200_OK,
        )



class OrganizerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizer]

    def get(self, request):
        events = Event.objects.filter(organizer=request.user)

        if request.user.is_superuser:
            events = Event.objects.all()

        booking_stats = Booking.objects.filter(
            event__in=events,
            status=Booking.Status.CONFIRMED,
        ).aggregate(
            total_bookings=Count("id"),
            total_seats=Coalesce(
                Sum("seats"),
                Value(0),
                output_field=IntegerField(),
            ),
        )

        return Response({
            "total_events": events.count(),
            "draft_events": events.filter(
                status=Event.Status.DRAFT
            ).count(),
            "published_events": events.filter(
                status=Event.Status.PUBLISHED
            ).count(),
            "cancelled_events": events.filter(
                status=Event.Status.CANCELLED
            ).count(),
            "total_confirmed_bookings": booking_stats[
                "total_bookings"
            ],
            "total_seats_booked": booking_stats["total_seats"],
        })


class OrganizerEventBookingsView(generics.ListAPIView):
    serializer_class = OrganizerBookingSerializer
    permission_classes = [IsAuthenticated, IsOrganizer]

    def get_queryset(self):
        event = get_object_or_404(
            Event.objects.all(),
            pk=self.kwargs["pk"],
        )

        if (
            not self.request.user.is_superuser
            and event.organizer_id != self.request.user.id
        ):
            raise PermissionDenied(
                "You can view bookings only for your own events."
            )

        return Booking.objects.filter(
            event=event
        ).select_related(
            "attendee"
        ).order_by("-created_at")
