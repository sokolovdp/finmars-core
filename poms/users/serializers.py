from __future__ import unicode_literals

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.utils import translation
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_perms
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from poms.api.fields import CurrentMasterUserDefault
from poms.users.models import MasterUser, UserProfile, GroupProfile, Member, AVAILABLE_APPS


class MasterUserField(serializers.HiddenField):
    def __init__(self, **kwargs):
        kwargs['default'] = CurrentMasterUserDefault()
        super(MasterUserField, self).__init__(**kwargs)


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
        queryset = queryset.filter(content_type__app_label__in=AVAILABLE_APPS)
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


class ObjectPermissionField(serializers.Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(ObjectPermissionField, self).__init__(**kwargs)

    def bind(self, field_name, parent):
        super(ObjectPermissionField, self).bind(field_name, parent)

    def to_representation(self, value):
        request = self.context['request']
        ctype = ContentType.objects.get_for_model(value)
        return {'%s.%s' % (ctype.app_label, p) for p in get_perms(request.user, value)}
        # return get_perms(request.user, value)


class GroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='groupprofile-detail')
    permissions = PermissionField(many=True)

    class Meta:
        model = GroupProfile
        fields = ['url', 'id', 'name', 'permissions']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['language', 'timezone']


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='user-detail')
    groups = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True)
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'first_name', 'last_name', 'groups', 'profile', ]
        read_only_fields = ['username', ]


class MasterUserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='masteruser-detail')

    # members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = MasterUser
        fields = ['url', 'id', 'currency', 'members']


class MemberSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='member-detail')
    # members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(pk__gt=0))

    class Meta:
        model = Member
        fields = ['url', 'id', 'master_user', 'user', 'is_owner', 'is_admin', 'join_date']
