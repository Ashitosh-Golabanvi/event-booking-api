
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOrganizer(BasePermission):
    """
    Allow event management only for organizers.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.role == "organizer"
            )
        )


class IsEventOrganizerOrReadOnly(BasePermission):
    """
    Allow safe read methods, but restrict event changes
    to the event's organizer or an admin.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or obj.organizer_id == request.user.id
            )
        )
