from __future__ import unicode_literals

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from poms.api.fields import CurrentMasterUserDefault
from poms.users.models import MasterUser, UserProfile, GroupProfile, Member


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
    original_password = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, max_length=128, style={'input_type': 'password'})

    def create(self, validated_data):
        # password = validated_data.get('password')
        # user.set_password()
        return validated_data


class ContentTypeSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='contenttype-detail')

    class Meta:
        model = ContentType
        fields = ['url', 'id', 'app_label', 'model']


class PermissionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='permission-detail')
    content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all())

    class Meta:
        model = Permission
        fields = ['url', 'id', 'content_type', 'codename']


class GroupProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupProfile
        fields = ['master_user', 'name']


class PermissionField(serializers.RelatedField):
    def to_internal_value(self, data):
        try:
            app_label, codename = data.split('.')
            return self.get_queryset().get(content_type__app_label=app_label, codename=codename)
        # except ObjectDoesNotExist:
        #     self.fail('does_not_exist', slug_name=self.slug_field, value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, obj):
        return '%s.%s' % (obj.content_type.app_label, obj.codename)


class GroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='group-detail')
    # permissions = serializers.PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True)
    # permissions = PermissionField(queryset=Permission.objects.all(), many=True)
    profile = GroupProfileSerializer()

    # real_name = serializers.CharField()
    # master_user = serializers.PrimaryKeyRelatedField(queryset=MasterUser.objects.all())
    # master_user = serializers.CharField()

    class Meta:
        model = Group
        fields = ['url', 'id', 'name', 'profile']


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
