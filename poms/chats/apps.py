from django.apps import AppConfig

from django.utils.translation import ugettext_lazy


class ChatsConfig(AppConfig):
    name = 'poms.chats'
    # label = 'poms'
    verbose_name = ugettext_lazy('Chats')

    def ready(self):
        # noinspection PyUnresolvedReferences
        import poms.chats.handlers
