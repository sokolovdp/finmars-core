from __future__ import unicode_literals

from poms.obj_perms.fields import PrimaryKeyRelatedFilteredWithObjectPermissionField
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.users.filters import OwnerByMasterUserFilter


class Strategy1Default(object):
    def set_context(self, serializer_field):
        request = serializer_field.context['request']
        self._master_user = request.user.master_user

    def __call__(self):
        return self._master_user.strategy1


class Strategy1Field(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Strategy1.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


class Strategy2Default(object):
    def set_context(self, serializer_field):
        request = serializer_field.context['request']
        self._master_user = request.user.master_user

    def __call__(self):
        return self._master_user.strategy2


class Strategy2Field(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Strategy2.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


class Strategy3Default(object):
    def set_context(self, serializer_field):
        request = serializer_field.context['request']
        self._master_user = request.user.master_user

    def __call__(self):
        return self._master_user.strategy3


class Strategy3Field(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Strategy3.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]
