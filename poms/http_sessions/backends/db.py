from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore as DjangoSessionStore


class SessionStore(DjangoSessionStore):
    @classmethod
    def get_model_class(cls):
        from poms.http_sessions.models import Session
        return Session

    def create_model_instance(self, data):
        obj = super(SessionStore, self).create_model_instance(data)

        try:
            user_id = int(data.get('_auth_user_id'))
        except (ValueError, TypeError):
            user_id = None
        if user_id:
            user_model = get_user_model()
            obj.user = user_model.objects.get(pk=user_id)

        obj.user_agent = data.get('user_agent', None)
        obj.user_ip = data.get('user_ip', None)

        return obj
