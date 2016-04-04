from __future__ import unicode_literals

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.utils import translation
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from poms.audit import history
from poms.users.fields import MasterUserField, get_master_user, get_member, GroupField
from poms.users.models import MasterUser, UserProfile, Group, Member, AVAILABLE_APPS


class LoginSerializer(AuthTokenSerializer):
    pass


class RegisterSerializer(AuthTokenSerializer):
    username = serializers.CharField(required=True, max_length=30)
    password = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'})

    def create(self, validated_data):
        username = validated_data.get('username')
        password = validated_data.get('password')

        user_model = get_user_model()

        if user_model.objects.filter(username=username).exists():
            msg = _('User already exist.')
            raise serializers.ValidationError(msg)

        user = user_model.objects.create_user(username=username, password=password)
        master_user = MasterUser.objects.create(user=user, language=translation.get_language())

        user = authenticate(username=username, password=password)

        validated_data['user'] = user
        return validated_data


class PasswordChangeSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'})

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        password = validated_data['password']
        if user.check_password(password):
            new_password = validated_data['new_password']
            user.set_password(new_password)
            return validated_data
        raise PermissionDenied(_('Invalid password'))


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
        request = self.context['request']
        ctype = ContentType.objects.get_for_model(value)
        # return {'%s.%s' % (ctype.app_label, p) for p in get_perms(request.user, value)}
        return []
        # return get_perms(request.user, value)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['language', 'timezone']


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='user-detail')
    groups = GroupField(many=True)  # TODO: filter groups in response JSON
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['url', 'id', 'first_name', 'last_name', 'groups', 'profile']
        # read_only_fields = ['username', ]

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        groups = validated_data.pop('groups')
        user = User.objects.create(**validated_data)
        user.groups = groups
        UserProfile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')
        profile = instance.profile

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        if 'groups' in validated_data:
            request = self.context['request']
            master_user = get_master_user(request)
            cur_groups = set(instance.groups.filter(profile__master_user=master_user))
            new_groups = set(validated_data['groups'])

            add_groups = new_groups - cur_groups
            del_groups = cur_groups - new_groups

            if add_groups:
                instance.groups.add(*add_groups)
            if del_groups:
                instance.groups.remove(*del_groups)

                # instance.groups = validated_data.get('groups', instance.groups)

        profile.language = profile_data.get('language', profile.language)
        profile.timezone = profile_data.get('timezone', profile.timezone)
        profile.save()

        return instance


class MasterUserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='masteruser-detail')
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = MasterUser
        fields = ['url', 'id', 'name', 'currency', 'is_current', 'members']

    def get_is_current(self, obj):
        request = self.context['request']
        return obj.id == get_master_user(request).id


class MemberSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='member-detail')
    master_user = MasterUserField()
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(pk__gt=0))
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = ['url', 'id', 'master_user', 'user', 'is_owner', 'is_admin', 'join_date', 'is_current']
        read_only_fields = ['user', 'is_owner']

    def get_is_current(self, obj):
        request = self.context['request']
        member = get_member(request)
        return obj.id == member.id


class GroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='group-detail')
    master_user = MasterUserField()
    permissions = PermissionField(many=True)

    class Meta:
        model = Group
        fields = ['url', 'id', 'master_user', 'name', 'permissions']
