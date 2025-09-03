import base64

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from poms.common.fields import (
    PrimaryKeyRelatedFilteredField,
    UserCodeOrPrimaryKeyRelatedField,
)
from poms.iam.models import AccessPolicy, Group, Role
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.models import MasterUser, Member
from poms_app import settings


class CurrentMasterUserDefault:
    requires_context = True

    def set_context(self, serializer_field):
        # Only one MasterUser per Space (scheme)
        self._master_user = MasterUser.objects.using(settings.DB_DEFAULT).first()

    def __call__(self, serializer_field):
        self.set_context(serializer_field)

        return self._master_user


class CurrentUserDefaultLocal:
    requires_context = True

    def set_context(self, serializer_field):
        request = serializer_field.context["request"]
        user = request.user
        self._user = user

    def __call__(self, serializer_field):
        self.set_context(serializer_field)
        return self._user


class MasterUserField(serializers.HiddenField):
    def __init__(self, **kwargs):
        kwargs["default"] = CurrentMasterUserDefault()
        super().__init__(**kwargs)


class CurrentUserField(serializers.HiddenField):
    def __init__(self, **kwargs):
        kwargs["default"] = CurrentUserDefaultLocal()
        super().__init__(**kwargs)


class CurrentMemberDefault:
    requires_context = True

    def set_context(self, serializer_field):
        request = serializer_field.context["request"]
        member = request.user.member
        self._member = member

    def __call__(self, serializer_field):
        self.set_context(serializer_field)

        return getattr(self, "_member", None)


class HiddenMemberField(serializers.HiddenField):
    def __init__(self, **kwargs):
        kwargs["default"] = CurrentMemberDefault()
        super().__init__(**kwargs)


class HiddenUserField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs["default"] = CurrentUserDefault()
        kwargs.setdefault("read_only", True)

        print(f"HIDDEN USER FILD? {kwargs['default']}")

        super().__init__(**kwargs)


class MemberField(PrimaryKeyRelatedFilteredField):
    queryset = Member.objects
    filter_backends = [OwnerByMasterUserFilter]


class UserField(PrimaryKeyRelatedFilteredField):
    queryset = User.objects.all()


class GroupField(UserCodeOrPrimaryKeyRelatedField):
    queryset = Group.objects.all()


class RoleField(UserCodeOrPrimaryKeyRelatedField):
    queryset = Role.objects.all()


class AccessPolicyField(UserCodeOrPrimaryKeyRelatedField):
    queryset = AccessPolicy.objects.all()


class Base64BinaryField(serializers.Field):
    def to_representation(self, value):
        if value is None:
            return None
        return base64.b64encode(value).decode("utf-8")

    def to_internal_value(self, data):
        if data is None:
            return None
        try:
            return base64.b64decode(data)
        except Exception as e:
            raise serializers.ValidationError("Invalid Base64-encoded data.") from e
