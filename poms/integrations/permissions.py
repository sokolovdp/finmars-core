from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions


class BloombergConfigured(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        master_user = request.user.master_user
        try:
            return master_user.bloomberg_config.is_ready
        except ObjectDoesNotExist:
            pass
        return False

