from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class NotificationsConfig(AppConfig):
    name = 'poms.notifications'
    verbose_name = _('Notification')

    # def ready(self):
    #     from poms.notifications.models import notify_handler
    #     from poms.notifications.signals import notify
    #     notify.connect(notify_handler, dispatch_uid='notifications.notify_handler')
