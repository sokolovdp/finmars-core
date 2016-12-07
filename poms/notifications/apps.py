from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class NotificationsConfig(AppConfig):
    name = 'poms.notifications'
    verbose_name = ugettext_lazy('Notification')

    def ready(self):
        # noinspection PyUnresolvedReferences
        import poms.notifications.handlers
