from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.audit import history
from poms.users.filters import OwnerByMasterUserFilter
from poms.users.models import Member, AVAILABLE_APPS


def get_master_user(request, master_user_id=None):
    user = request.user
    if hasattr(user, '_cached_master_user'):
        return user._cached_master_user
    if master_user_id is None:
        master_user_id = request.GET.get('master_user_id', None)
    if master_user_id is None:
        master_user_id = request.session.get('master_user_id', None)
    try:
        if master_user_id is None:
            if settings.DEV:
                member = user.member_set.first()
                master_user = member.master_user
            else:
                raise NotFound()
        else:
            master_user = user.member_set.get(pk=master_user_id)
        user._cached_master_user = master_user
        return master_user
    except ObjectDoesNotExist:
        raise NotFound()


def set_master_user(request, master_user_id):
    old_master_user_id = request.session.get('master_user_id', None)
    if old_master_user_id != master_user_id:
        if master_user_id is None:
            del request.session['master_user_id']
        else:
            request.session['master_user_id'] = master_user_id


def get_member(request, master_user_id=None):
    user = request.user
    if hasattr(user, '_cached_member'):
        return user._cached_member
    try:
        master_user = get_master_user(request, master_user_id)
        master_user_id = master_user.id
        member = Member.objects.get(user=request.user, master_user=master_user_id)
        user._cached_member = member
        return member
    except ObjectDoesNotExist:
        raise NotFound()


def is_admin(request, master_user_id=None):
    try:
        member = get_member(request, master_user_id)
        return member.is_admin
    except NotFound:
        return False


def is_owner(request, master_user_id=None):
    try:
        member = get_member(request, master_user_id)
        return member.is_admin
    except NotFound:
        return False


def is_admin_role(request, master_user_id=None):
    try:
        member = get_member(request, master_user_id)
        return member.is_admin or member.is_owner
    except NotFound:
        return False


class CurrentMasterUserDefault(object):
    def set_context(self, serializer_field):
        request = serializer_field.context['request']
        self._master_user = get_master_user(request)

    def __call__(self):
        return self._master_user


class MasterUserField(serializers.HiddenField):
    def __init__(self, **kwargs):
        kwargs['default'] = CurrentMasterUserDefault()
        super(MasterUserField, self).__init__(**kwargs)


class CurrentMemberDefault(object):
    def set_context(self, serializer_field):
        request = serializer_field.context['request']
        self._member = get_member(request)

    def __call__(self):
        return self._member


class HiddenMemberField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        kwargs['default'] = CurrentMemberDefault()
        kwargs['read_only'] = True
        super(HiddenMemberField, self).__init__(**kwargs)


class MemberField(FilteredPrimaryKeyRelatedField):
    queryset = Member.objects
    filter_backends = [OwnerByMasterUserFilter]


class GroupOwnerByMasterUserFilter(OwnerByMasterUserFilter):
    def filter_queryset(self, request, queryset, view):
        # print(get_master_user(request))
        return queryset.filter(profile__master_user=get_master_user(request))


class UserField(FilteredPrimaryKeyRelatedField):
    queryset = User.objects.all()


class GroupField(FilteredPrimaryKeyRelatedField):
    queryset = Group.objects.all()
    filter_backends = [GroupOwnerByMasterUserFilter]


class PermissionField(serializers.SlugRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault('slug_field', 'codename')
        if 'queryset' not in kwargs:
            kwargs['queryset'] = Permission.objects.all()
        super(PermissionField, self).__init__(**kwargs)

    def get_queryset(self):
        queryset = super(PermissionField, self).get_queryset()
        queryset = queryset.select_related('content_type').filter(content_type__app_label__in=AVAILABLE_APPS)
        return queryset

    def to_internal_value(self, data):
        try:
            app_label, codename = data.split('.')
            return self.get_queryset().get(content_type__app_label=app_label, codename=codename)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, obj):
        return '%s.%s' % (obj.content_type.app_label, obj.codename)


class GrantedPermissionField(serializers.Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(GrantedPermissionField, self).__init__(**kwargs)

    def bind(self, field_name, parent):
        super(GrantedPermissionField, self).bind(field_name, parent)

    def to_representation(self, value):
        if history.is_historical_proxy(value):
            return []
        user = self.context['request'].user
        return user.get_all_permissions(value)
