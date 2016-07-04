from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class NotificationsConfig(AppConfig):
    name = 'poms.notifications'
    verbose_name = _('Notification')

    def ready(self):
        # noinspection PyUnresolvedReferences
        import poms.notifications.handlers
