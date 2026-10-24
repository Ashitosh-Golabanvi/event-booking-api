
from django.urls import path

from .views import (
    EventListCreateView,
    EventDetailView,
    BookingListCreateView,
    BookingCancelView,
    EventManageDetailView,
    EventPublishView,
    EventCancelView,
    OrganizerDashboardView,
    OrganizerEventBookingsView,
)


urlpatterns = [
    path("", EventListCreateView.as_view(), name="event-list-create"),
    path("<int:pk>/", EventDetailView.as_view(), name="event-detail"),
    path("bookings/", BookingListCreateView.as_view(), name="booking-list-create"),
    path("bookings/<str:booking_reference>/cancel/", BookingCancelView.as_view(), name="booking-cancel",),
    path("<int:pk>/manage/", EventManageDetailView.as_view(), name="event-manage",),
    path("<int:pk>/publish/", EventPublishView.as_view(), name="event-publish",),
    path("<int:pk>/cancel/", EventCancelView.as_view(), name="event-cancel",),
    path("organizer/dashboard/", OrganizerDashboardView.as_view(), name="organizer-dashboard",),
    path("<int:pk>/bookings/", OrganizerEventBookingsView.as_view(), name="organizer-event-bookings",),
]

