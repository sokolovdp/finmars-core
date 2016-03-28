from django.apps import AppConfig

from django.utils.translation import ugettext_lazy as _


class U2UMessagesConfig(AppConfig):
    name = 'poms.u2u_messages'
    # label = 'poms'
    verbose_name = _('Messages')
