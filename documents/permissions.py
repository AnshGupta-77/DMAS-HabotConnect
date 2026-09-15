from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import User


class DocumentObjectPermission(BasePermission):
    """Object-level checks for document CRUD. Queryset is already role-scoped,
    so reaching has_object_permission implies the user can see the document."""

    def has_permission(self, request, view):
        if request.method == "POST":
            return bool(request.user and request.user.is_authenticated and request.user.role != User.Role.REVIEWER)
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in SAFE_METHODS:
            return True
        if user.role == User.Role.ADMIN:
            return True
        if request.method in ("PATCH", "PUT"):
            return obj.created_by_id == user.id
        if request.method == "DELETE":
            return obj.created_by_id == user.id and obj.status == obj.Status.DRAFT
        return False
