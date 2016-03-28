from django.contrib.messages.storage.base import BaseStorage, Message
from django.contrib.messages.storage.cookie import CookieStorage
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils import timezone
from django.utils.encoding import force_text

from poms.notifications.models import Notification


# Can user is null  middleware process_response if used in Rest Framework authtoken?

class Storage(BaseStorage):
    def _get(self, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated():
            queryset = Notification.objects.filter(read_date__isnull=True)
            ret = []
            for n in queryset:
                message = Message(n.level, force_text(n), None)
                message.id = n.pk
                ret.append(message)
                print(0, getattr(message, 'id', None), message)
            return ret, True
        else:
            return [], False

    def _store(self, messages, response, *args, **kwargs):
        if messages:
            user = self.request.user
            if user.is_authenticated():
                for message in messages:
                    print(1, getattr(message, 'id', None), message)
                    if not hasattr(message, 'id'):
                        Notification.objects.create(
                            recipient=user,
                            level=message.level,
                            message=message
                        )
        else:
            Notification.objects.filter(read_date__isnull=True).update(read_date=timezone.now())
        return []


class NFallbackStorage(FallbackStorage):
    storage_classes = (Storage, CookieStorage)
