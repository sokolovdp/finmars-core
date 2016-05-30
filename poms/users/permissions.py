from rest_framework.permissions import BasePermission


class SuperUserOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.member.is_superuser

    def has_object_permission(self, request, view, obj):
        return request.user.member.is_superuser
