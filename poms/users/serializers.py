from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from poms.common.fields import DateTimeTzAwareField
from poms.currencies.fields import CurrencyField
from poms.users.fields import MasterUserField
from poms.users.models import MasterUser, UserProfile, Group, Member, TIMEZONE_CHOICES


class PingSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)
    version = serializers.CharField(read_only=True)
    is_authenticated = serializers.BooleanField(read_only=True)
    is_anonymous = serializers.BooleanField(read_only=True)
    now = serializers.DateTimeField(read_only=True)


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


class UserProfileSerializer(serializers.ModelSerializer):
    language = serializers.ChoiceField(choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    timezone = serializers.ChoiceField(choices=TIMEZONE_CHOICES)

    class Meta:
        model = UserProfile
        fields = ['language', 'timezone']


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='user-detail')
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'first_name', 'last_name', 'email', 'profile']

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        user = User.objects.create(**validated_data)
        user.profile.language = profile_data.get('language', settings.LANGUAGE_CODE)
        user.profile.timezone = profile_data.get('timezone', settings.TIME_ZONE)
        user.profile.save()
        # UserProfile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        if profile_data:
            profile = instance.profile
            profile.language = profile_data.get('language', profile.language)
            profile.timezone = profile_data.get('timezone', profile.timezone)
            profile.save()

        return instance


class UserSetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(allow_null=False, allow_blank=False, required=True, write_only=True,
                                     style={'input_type': 'password'})
    new_password = serializers.CharField(allow_null=False, allow_blank=False, required=True, write_only=True,
                                         style={'input_type': 'password'})

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['password']):
            raise serializers.ValidationError({'password': 'bad password'})
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        user.set_password(validated_data['new_password'])
        return validated_data

    def update(self, instance, validated_data):
        return self.create(validated_data)


class UserUnsubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_null=False, allow_blank=False, required=True, write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if attrs['email'] != user.email:
            raise serializers.ValidationError({'email': 'Invalid email'})
        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        return validated_data

    def update(self, instance, validated_data):
        return self.create(validated_data)


class MasterUserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='masteruser-detail')
    currency = CurrencyField()
    language = serializers.ChoiceField(choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    timezone = serializers.ChoiceField(choices=TIMEZONE_CHOICES)
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = MasterUser
        fields = ['url', 'id', 'name', 'currency', 'language', 'timezone', 'is_current']

    def get_is_current(self, obj):
        request = self.context['request']
        # master_user = get_master_user(request)
        master_user = request.user.master_user
        return obj.id == master_user.id


class MasterUserSetCurrentSerializer(serializers.Serializer):
    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return self.create(validated_data)


class MemberSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='member-detail')
    master_user = MasterUserField()
    is_current = serializers.SerializerMethodField()
    join_date = DateTimeTzAwareField()

    class Meta:
        model = Member
        fields = ['url', 'id', 'master_user', 'join_date', 'is_owner', 'is_admin', 'is_superuser', 'is_current',
                  'is_deleted', 'username', 'first_name', 'last_name', 'display_name', 'email', ]
        read_only_fields = ['master_user', 'join_date', 'is_superuser', 'is_current', 'is_deleted', 'username',
                            'first_name', 'last_name', 'display_name', 'email', ]

    def get_is_current(self, obj):
        member = self.context['request'].user.member
        return obj.id == member.id


class GroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='group-detail')
    master_user = MasterUserField()

    class Meta:
        model = Group
        fields = ['url', 'id', 'master_user', 'name']
