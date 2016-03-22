from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UsersConfig(AppConfig):
    name = 'poms.users'
    verbose_name = _('Poms users')

    def ready(self):
        from django.contrib.auth.models import Group

        def get_real_name(self):
            profile = getattr(self, 'profile', None)
            if profile:
                return profile.name
            return self.name

        def set_real_name(self, value):
            profile = self.profile
            if profile:
                profile.name = value

        Group.add_to_class("real_name", property(get_real_name, set_real_name))

        def get_master_user(self):
            profile = getattr(self, 'profile', None)
            if profile:
                return profile.master_user
            return self.name

        def set_master_user(self, value):
            profile = self.profile
            if profile:
                profile.master_user = value

        Group.add_to_class("master_user", property(get_master_user, set_master_user))
