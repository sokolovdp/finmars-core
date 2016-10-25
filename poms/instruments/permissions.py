from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from poms.instruments.models import GeneratedEvent


class GeneratedEventPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        notification_class = obj.event_schedule.notification_class
        show_notification, apply_default, needed_reaction = notification_class.check_date(
            None, obj.effective_date, obj.notification_date)
        return obj.status == GeneratedEvent.NEW and needed_reaction

