from rest_framework.permissions import BasePermission, SAFE_METHODS


class SuperUserOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.member.is_superuser

    def has_object_permission(self, request, view, obj):
        return request.user.member.is_superuser


class SuperUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method.upper() in SAFE_METHODS:
            return True
        return request.user.member.is_superuser

    def has_object_permission(self, request, view, obj):
        if request.method.upper() in SAFE_METHODS:
            return True
        return request.user.member.is_superuser
