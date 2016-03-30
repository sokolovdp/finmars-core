from django.apps import AppConfig

from django.utils.translation import ugettext_lazy as _


class ChatsConfig(AppConfig):
    name = 'poms.chats'
    # label = 'poms'
    verbose_name = _('Chats')
