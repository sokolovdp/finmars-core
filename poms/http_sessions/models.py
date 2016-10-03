from __future__ import unicode_literals

import uuid

from django.conf import settings
from django.contrib.sessions.base_session import AbstractBaseSession
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy

from poms.http_sessions.backends.db import SessionStore


@python_2_unicode_compatible
class Session(AbstractBaseSession):
    id = models.UUIDField(unique=True, default=uuid.uuid4, verbose_name=ugettext_lazy('public id'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, verbose_name=ugettext_lazy('user'))
    user_agent = models.CharField(max_length=255, null=True, blank=True, verbose_name=ugettext_lazy('user agent'))
    user_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name=ugettext_lazy('user ip'))

    class Meta:
        verbose_name = ugettext_lazy('session')
        verbose_name_plural = ugettext_lazy('sessions')
        ordering = ['user', 'expire_date']

    @classmethod
    def get_session_store_class(cls):
        return SessionStore

    def __str__(self):
        return '%s:%s:%s' % (self.user, self.user_ip, self.user_agent)

    @property
    def human_user_agent(self):
        if not self.user_agent:
            return None
        try:
            from user_agents import parse
            ret = parse(self.user_agent)
            return str(ret)
        except ImportError:
            return None
